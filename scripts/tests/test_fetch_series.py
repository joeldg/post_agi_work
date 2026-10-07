"""Tests for scripts/fetch_series.py (spec 7.3). Saved responses only; no network."""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import fetch_series  # noqa: E402

HTTP = HERE / "fixtures" / "http"
NOW = "2026-10-06T12:00:00-07:00"


def body(name):
    return (HTTP / name).read_text(encoding="utf-8")


def fake_get(routes):
    """get(url, data=None) answering from {url substring: body}; an unknown url raises like a network error."""
    def get(url, data=None):
        for key, text in routes.items():
            if key in url:
                return text
        raise OSError(f"no route for {url}")
    return get


def claims_with(series):
    return {"claims": [{"id": "J0", "indicators": [{"id": "J0-a", "series": series}]}]}


class Root:
    def __init__(self, series, old=None):
        self.series = series
        self.old = old or {}

    def __enter__(self):
        self.path = Path(tempfile.mkdtemp(prefix="jobs-fetch-"))
        (self.path / "claims.json").write_text(json.dumps(claims_with(self.series)), encoding="utf-8")
        (self.path / "series").mkdir()
        for sid, obs in self.old.items():
            doc = {"id": sid, "url": "u", "fetched": "2026-09-01T00:00:00-07:00", "status": "ok", "error": None,
                   "observations": obs}
            (self.path / "series" / fetch_series.file_name(sid)).write_text(json.dumps(doc), encoding="utf-8")
        return self.path

    def __exit__(self, *exc):
        shutil.rmtree(self.path, ignore_errors=True)


def read(root, sid):
    return json.loads((root / "series" / fetch_series.file_name(sid)).read_text(encoding="utf-8"))


class Parse(unittest.TestCase):
    def test_fred_parses_and_skips_missing(self):
        obs = fetch_series.fetch_one("fred:DFII10", fake_get({"fredgraph.csv?id=DFII10": body("fred_DFII10.csv")}))
        self.assertEqual(obs, [["2015-01-02", 0.6], ["2026-09-30", 1.8]])   # before START and "." rows dropped

    def test_bls_periods(self):
        obs = fetch_series.fetch_one("bls:JTS510000000000000HIR", fake_get({"api.bls.gov": body("bls_ok.json")}))
        self.assertEqual(obs, [["2025-Q3", 1.9], ["2026-02", 2.1], ["2026-08", 1.6]])  # sorted; M13 skipped

    def test_bls_refusal_raises(self):
        with self.assertRaisesRegex(fetch_series.FetchError, "REQUEST_NOT_PROCESSED"):
            fetch_series.fetch_one("bls:X", fake_get({"api.bls.gov": body("bls_refused.json")}))

    def test_html_body_raises(self):
        with self.assertRaises(fetch_series.FetchError):
            fetch_series.fetch_one("fred:DFII10", fake_get({"fredgraph": body("captcha.html")}))

    def test_unsupported_prefix_raises(self):
        with self.assertRaisesRegex(fetch_series.FetchError, "no keyless source"):
            fetch_series.fetch_one("stooq:acn.us", fake_get({}))

    def test_series_ids(self):
        doc = {"claims": [{"indicators": [{"series": ["fred:B", "fred:A"]}, {"series": None}]},
                          {"indicators": [{"series": ["fred:A"]}]}]}
        self.assertEqual(fetch_series.series_ids(doc), ["fred:A", "fred:B"])


class Run(unittest.TestCase):
    def test_writes_series_and_releases(self):
        with Root(["fred:DFII10"]) as root:
            summary = fetch_series.run(root, fake_get({"fredgraph": body("fred_DFII10.csv")}), NOW)
            self.assertEqual(summary, {"ok": ["fred:DFII10"], "stale": []})
            doc = read(root, "fred:DFII10")
            self.assertEqual((doc["status"], doc["error"], doc["fetched"]), ("ok", None, NOW))
            rel = json.loads((root / "series" / "releases.json").read_text(encoding="utf-8"))
            self.assertEqual(rel["series"][0]["new"], [["2015-01-02", 0.6], ["2026-09-30", 1.8]])
            self.assertEqual(rel["series"][0]["latest"], ["2026-09-30", 1.8])

    def test_html_body_keeps_last_good(self):
        old = {"fred:DFII10": [["2026-08-29", 1.7]]}
        with Root(["fred:DFII10"], old) as root:
            summary = fetch_series.run(root, fake_get({"fredgraph": body("captcha.html")}), NOW)
            self.assertEqual(summary["stale"], ["fred:DFII10"])
            doc = read(root, "fred:DFII10")
            self.assertEqual((doc["status"], doc["observations"]), ("stale", [["2026-08-29", 1.7]]))
            self.assertTrue(doc["error"])

    def test_bls_refusal_is_stale(self):
        with Root(["bls:X"]) as root:
            summary = fetch_series.run(root, fake_get({"api.bls.gov": body("bls_refused.json")}), NOW)
            self.assertEqual(summary, {"ok": [], "stale": ["bls:X"]})
            self.assertEqual(read(root, "bls:X")["observations"], [])

    def test_one_failure_never_stops_the_others(self):
        with Root(["bls:X", "fred:DFII10"]) as root:
            summary = fetch_series.run(root, fake_get({"fredgraph": body("fred_DFII10.csv")}), NOW)
            self.assertEqual(summary, {"ok": ["fred:DFII10"], "stale": ["bls:X"]})

    def test_releases_new_and_revised(self):
        csv = "observation_date,X\n2026-08-01,1.1\n2026-09-01,1.2\n"
        old = {"fred:X": [["2026-08-01", 1.0]]}
        with Root(["fred:X"], old) as root:
            fetch_series.run(root, fake_get({"fredgraph": csv}), NOW)
            rel = json.loads((root / "series" / "releases.json").read_text(encoding="utf-8"))["series"][0]
            self.assertEqual(rel["new"], [["2026-09-01", 1.2]])
            self.assertEqual(rel["revised"], [["2026-08-01", 1.0, 1.1]])

    def test_window_keeps_older_observations(self):
        # The 2026-10-06 review's I6: BLS answers only the last 10 years, so each pull would drop the oldest year
        # and, by 2031, every pre-2022 value the marks are measured against.
        old = {"bls:JTS510000000000000HIR": [["2015-01", 3.0], ["2016-01", 3.1], ["2026-07", 9.9]]}
        with Root(["bls:JTS510000000000000HIR"], old) as root:
            fetch_series.run(root, fake_get({"api.bls.gov": body("bls_ok.json")}), NOW)
            obs = read(root, "bls:JTS510000000000000HIR")["observations"]
            self.assertEqual(obs, [["2015-01", 3.0], ["2016-01", 3.1], ["2025-Q3", 1.9], ["2026-02", 2.1], ["2026-08", 1.6]])

    def test_empty_bls_answer_is_stale(self):
        # I7: "Series does not exist" comes back as REQUEST_SUCCEEDED with no data, and must not wipe the file.
        empty = '{"status":"REQUEST_SUCCEEDED","message":["Series does not exist for Series X"],"Results":{"series":[{"seriesID":"X","data":[]}]}}'
        with Root(["bls:X"], {"bls:X": [["2026-07", 1.0]]}) as root:
            summary = fetch_series.run(root, fake_get({"api.bls.gov": empty}), NOW)
            self.assertEqual(summary["stale"], ["bls:X"])
            self.assertEqual(read(root, "bls:X")["observations"], [["2026-07", 1.0]])

    def test_header_only_fred_answer_is_stale(self):
        with Root(["fred:X"], {"fred:X": [["2026-07-01", 1.0]]}) as root:
            summary = fetch_series.run(root, fake_get({"fredgraph": "observation_date,X\n"}), NOW)
            self.assertEqual(summary["stale"], ["fred:X"])

    def test_bls_refusal_keeps_last_good(self):
        with Root(["bls:X"], {"bls:X": [["2026-07", 1.0]]}) as root:
            fetch_series.run(root, fake_get({"api.bls.gov": body("bls_refused.json")}), NOW)
            self.assertEqual(read(root, "bls:X")["observations"], [["2026-07", 1.0]])

    def test_malformed_id_exits_2(self):
        with Root(["fred"]) as root:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(fetch_series.main(["--root", str(root)], get=fake_get({})), 2)
            self.assertIn("fred", err.getvalue())


if __name__ == "__main__":
    unittest.main()
