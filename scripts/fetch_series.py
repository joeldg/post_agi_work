"""Pull the pinned official series named in claims.json (spec 7.3). Standard library only.

    python3 scripts/fetch_series.py [--root DIR]

Writes series/<prefix>__<id>.json for every series id in claims.json and series/releases.json (what is new or
revised since the files on disk). Sources, all keyless:
  fred:<ID>  FRED's CSV download, https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>
  bls:<ID>   the BLS public API v1 (no key; at most 10 years a request, 25 requests a day)
A series that fails keeps its last good observations and is marked "stale"; the run carries on and exits 0.
stooq: and basket: ids are valid in claims.json but have no keyless source in v1 (Stooq now answers with a
browser challenge), so they read as stale. A malformed id exits 2.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jobslib import SERIES_PREFIXES, dump_json, load_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
START = "2015-01-01"
BLS_YEARS = 10
USER_AGENT = "post_agi_work fetch_series (+https://github.com/joeldg/post_agi_work)"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
BLS_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
SAFE = re.compile(r"[^A-Za-z0-9._-]")


class FetchError(Exception):
    pass


def http_get(url: str, data: bytes | None = None) -> str:
    headers = {"User-Agent": USER_AGENT}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def file_name(sid: str) -> str:
    prefix, rest = sid.split(":", 1)
    return f"{prefix}__{SAFE.sub('_', rest)}.json"


def valid_id(sid) -> bool:
    if not isinstance(sid, str) or ":" not in sid:
        return False
    prefix, rest = sid.split(":", 1)
    return prefix in SERIES_PREFIXES and bool(rest.strip())


def series_ids(claims: dict) -> list:
    ids = set()
    for c in claims.get("claims") or []:
        for ind in c.get("indicators") or []:
            ids.update(ind.get("series") or [])
    return sorted(ids)


def _fred(code: str, get) -> list:
    text = get(FRED_URL.format(code))
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) != 2 or rows[0][0] not in ("observation_date", "DATE"):
        raise FetchError(f"fred:{code}: unexpected body (not FRED's CSV)")
    out = []
    for row in rows[1:]:
        if len(row) != 2 or row[1] in (".", ""):
            continue
        if row[0] < START:
            continue
        try:
            out.append([row[0], float(row[1])])
        except ValueError:
            raise FetchError(f"fred:{code}: bad value {row[1]!r} on {row[0]}")
    return out


def bls_period(year: str, period: str) -> str | None:
    """'M02' -> 'YYYY-02', 'Q03' -> 'YYYY-Q3', 'A01' -> 'YYYY'; M13 (the annual average) -> None."""
    if period.startswith("M") and period != "M13":
        return f"{year}-{period[1:]}"
    if period.startswith("Q") and period[1:].isdigit() and 1 <= int(period[1:]) <= 4:
        return f"{year}-Q{int(period[1:])}"
    if period.startswith("A"):
        return year
    return None


def _bls(code: str, get, end_year: int) -> list:
    payload = json.dumps({"seriesid": [code], "startyear": str(end_year - BLS_YEARS + 1),
                          "endyear": str(end_year)}).encode()
    text = get(BLS_URL, payload)
    try:
        doc = json.loads(text)
    except ValueError:
        raise FetchError(f"bls:{code}: unexpected body (not JSON)")
    if doc.get("status") != "REQUEST_SUCCEEDED":
        raise FetchError(f"bls:{code}: {doc.get('status')}: {' '.join(doc.get('message') or [])}".strip())
    series = (doc.get("Results") or {}).get("series") or []
    if not series:
        raise FetchError(f"bls:{code}: no series in the answer")
    out = []
    for d in series[0].get("data") or []:
        when = bls_period(str(d.get("year")), str(d.get("period")))
        if when is None or when[:4] < START[:4]:
            continue
        try:
            out.append([when, float(d["value"])])
        except (KeyError, ValueError):
            continue
    return sorted(out)


def fetch_one(sid: str, get, end_year: int | None = None) -> list:
    prefix, code = sid.split(":", 1)
    if prefix == "fred":
        return _fred(code, get)
    if prefix == "bls":
        return _bls(code, get, end_year or datetime.now().year)
    raise FetchError(f"{sid}: no keyless source for {prefix}: in v1")


def _old(path: Path) -> dict | None:
    try:
        return load_json(path)
    except (OSError, ValueError):
        return None


def run(root: Path, get=http_get, now: str | None = None) -> dict:
    root = Path(root)
    now = now or datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds")
    ids = series_ids(load_json(root / "claims.json"))
    bad = [s for s in ids if not valid_id(s)]
    if bad:
        raise ValueError("malformed series id(s): " + ", ".join(map(str, bad)))
    (root / "series").mkdir(exist_ok=True)
    summary, releases = {"ok": [], "stale": []}, []
    for sid in ids:
        path = root / "series" / file_name(sid)
        old = _old(path) or {}
        old_obs = old.get("observations") or []
        try:
            obs = fetch_one(sid, get, int(now[:4]))
            doc = {"id": sid, "url": _url(sid), "fetched": now, "status": "ok", "error": None, "observations": obs}
            summary["ok"].append(sid)
        except (FetchError, OSError, ValueError) as e:
            obs = old_obs
            doc = {"id": sid, "url": _url(sid), "fetched": old.get("fetched"), "status": "stale", "error": str(e),
                   "observations": obs}
            summary["stale"].append(sid)
        path.write_text(dump_json(doc), encoding="utf-8")
        before = {d: v for d, v in old_obs}
        releases.append({
            "id": sid, "status": doc["status"],
            "new": [[d, v] for d, v in obs if d not in before] if doc["status"] == "ok" else [],
            "revised": [[d, before[d], v] for d, v in obs if d in before and before[d] != v] if doc["status"] == "ok" else [],
            "latest": obs[-1] if obs else None,
        })
    (root / "series" / "releases.json").write_text(dump_json({"generated": now, "series": releases}), encoding="utf-8")
    return summary


def _url(sid: str) -> str:
    prefix, code = sid.split(":", 1)
    return {"fred": FRED_URL.format(code), "bls": BLS_URL + code}.get(prefix, "")


def main(argv: list | None = None, get=http_get) -> int:
    ap = argparse.ArgumentParser(description="Pull the pinned series named in claims.json.")
    ap.add_argument("--root", default=str(ROOT), help="plugin repo root")
    a = ap.parse_args(argv)
    try:
        summary = run(Path(a.root), get)
    except ValueError as e:
        print(f"fetch_series: {e}", file=sys.stderr)
        return 2
    print(f"fetch_series: {len(summary['ok'])} ok, {len(summary['stale'])} stale")
    for sid in summary["stale"]:
        print(f"WARN stale: {sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
