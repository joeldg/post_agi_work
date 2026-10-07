"""Tests for scripts/apply_edition.py: the writer stage's deterministic half (spec 7.2, Write)."""
import contextlib
import io
import json
import shutil
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import apply_edition  # noqa: E402
import check_plugin  # noqa: E402
import jobslib  # noqa: E402
from scripts.tests.test_check_plugin import BASE, make_repo  # noqa: E402


def payload(date="2026-10-22"):
    ed = json.loads((BASE / "editions/2026-10-15.json").read_text(encoding="utf-8"))
    ed["date"] = date
    ed["window"] = {"from": "2026-10-16", "to": date}
    ed["moves"] = [{"id": "J5", "from": "no-clear-sign", "to": "emerging", "why": "Trades pay beats the comparison.",
                    "evidence": ["e1"], "by": "run"}]
    ed["pendingOwner"] = [{"id": "J4", "from": "supported", "to": "established", "why": "Two quarters of official data.",
                           "evidence": ["e2"]}]
    for s in ed["strip"]:
        s["prev"] = s["status"]
    ed["strip"][5]["status"] = "emerging"
    row = {"date": date, "from": "no-clear-sign", "to": "emerging", "why": "Trades pay beats the comparison.",
           "evidence": [f"{date}#e1"], "by": "run"}
    return {"edition": ed, "claims": [{"id": "J5", "status": "emerging", "since": date, "pending": None, "history": row}]}


class Apply(unittest.TestCase):
    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_writes_edition_and_patch_and_checks_clean(self):
        problems = apply_edition.apply(self.root, payload())
        self.assertEqual(problems, [])
        self.assertTrue((self.root / "editions/2026-10-22.json").exists())
        claims = json.loads((self.root / "claims.json").read_text(encoding="utf-8"))
        j5 = claims["claims"][5]
        self.assertEqual((j5["status"], j5["since"], j5["history"][-1]["to"]), ("emerging", "2026-10-22", "emerging"))
        self.assertEqual(check_plugin.check(self.root), [])

    def test_pending_kept_when_patch_omits_it(self):
        apply_edition.apply(self.root, payload())
        claims = json.loads((self.root / "claims.json").read_text(encoding="utf-8"))
        self.assertEqual(claims["claims"][4]["pending"]["to"], "established")

    def test_refuses_committed_edition(self):
        with self.assertRaisesRegex(ValueError, "editions/2026-10-15.json is already committed"):
            apply_edition.apply(self.root, payload("2026-10-15"))

    def test_refuses_fields_a_run_may_not_change(self):
        p = payload()
        p["claims"][0]["wording"] = "Reworded."
        with self.assertRaisesRegex(ValueError, "J5: a run may not set wording"):
            apply_edition.apply(self.root, p)

    def test_rerun_overwrites_its_own_uncommitted_edition(self):
        apply_edition.apply(self.root, payload())
        p = payload()
        p["edition"]["headline"] = "Second try"
        self.assertEqual(apply_edition.apply(self.root, p), [])
        ed = json.loads((self.root / "editions/2026-10-22.json").read_text(encoding="utf-8"))
        self.assertEqual(ed["headline"], "Second try")

    def test_rerun_does_not_stack_a_second_step(self):
        # The 2026-10-06 review's I2: a second attempt read the first attempt's claims.json and moved J5 again.
        apply_edition.apply(self.root, payload())
        self.assertEqual(apply_edition.apply(self.root, payload()), [])
        claims = json.loads((self.root / "claims.json").read_text(encoding="utf-8"))
        rows = [h for h in claims["claims"][5]["history"] if h["date"] == "2026-10-22"]
        self.assertEqual(len(rows), 1)

    def signed(self, pl):
        pl["checksum"] = jobslib.payload_checksum({"edition": pl["edition"], "claims": pl["claims"]})
        return pl

    def test_main_refuses_a_payload_changed_in_transit(self):
        # The 2026-10-06 review's I9: an agent retypes the payload, so a changed word must be caught.
        pl = self.signed(payload())
        pl["edition"]["evidence"][0]["text"] = pl["edition"]["evidence"][0]["text"].replace("1", "2", 1) + " "
        path = self.root / "payload.json"
        path.write_text(json.dumps(pl), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(apply_edition.main([str(path), "--root", str(self.root)]), 2)
        self.assertIn("checksum", out.getvalue())
        self.assertFalse((self.root / "editions/2026-10-22.json").exists())

    def test_main_refuses_an_unsigned_payload(self):
        path = self.root / "payload.json"
        path.write_text(json.dumps(payload()), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(apply_edition.main([str(path), "--root", str(self.root)]), 2)
        self.assertIn("checksum", out.getvalue())

    def test_checksum_ignores_key_order_but_not_values(self):
        a = {"edition": {"x": 1.5, "y": ["a", "b"]}, "claims": []}
        b = {"claims": [], "edition": {"y": ["a", "b"], "x": 1.5}}
        self.assertEqual(jobslib.payload_checksum(a), jobslib.payload_checksum(b))
        self.assertNotEqual(jobslib.payload_checksum(a), jobslib.payload_checksum({"edition": {"x": 1.5, "y": ["a", "c"]}, "claims": []}))

    def test_main_exit_codes(self):
        path = self.root / "payload.json"
        path.write_text(json.dumps(self.signed(payload())), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(apply_edition.main([str(path), "--root", str(self.root)]), 0)
        self.assertIn("CHECK OK", out.getvalue())
        bad = payload("2026-10-29")
        bad["edition"]["strip"] = bad["edition"]["strip"][:12]
        path.write_text(json.dumps(self.signed(bad)), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(apply_edition.main([str(path), "--root", str(self.root)]), 1)
        self.assertIn("strip must list J0 to J12 in order", out.getvalue())


if __name__ == "__main__":
    unittest.main()
