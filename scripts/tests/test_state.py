"""Tests for scripts/state.py: what a run starts from, read by code (spec 7.2)."""
import json
import shutil
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import state  # noqa: E402
from scripts.tests.test_check_plugin import apply_ops, make_repo  # noqa: E402


class State(unittest.TestCase):
    def setUp(self):
        self.root = make_repo()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_prev_is_newest_edition_before_date(self):
        s = state.state(self.root, "2026-10-22")
        self.assertEqual(s["prev"]["date"], "2026-10-15")
        self.assertEqual([x["status"] for x in s["prev"]["strip"]][3:5], ["emerging", "supported"])
        self.assertEqual(s["claimsVersion"], "1.0")

    def test_same_day_edition_is_not_prev(self):
        self.assertEqual(state.state(self.root, "2026-10-15")["prev"]["date"], "2026-10-08")

    def test_no_prev_before_first_edition(self):
        self.assertIsNone(state.state(self.root, "2026-10-01")["prev"])

    def test_claims_current_status_and_pending(self):
        s = state.state(self.root, "2026-10-22")
        j4 = s["claims"][4]
        self.assertEqual((j4["id"], j4["status"], j4["pending"]["to"]), ("J4", "supported", "established"))

    def test_owner_moves_since_prev(self):
        row = {"date": "2026-10-18", "from": "supported", "to": "established", "why": "Owner agreed.",
               "evidence": ["2026-10-15#e2"], "by": "owner"}
        apply_ops(self.root, [{"file": "claims.json", "append": ["claims", 4, "history"], "value": row},
                              {"file": "claims.json", "set": ["claims", 4, "status"], "value": "established"}])
        s = state.state(self.root, "2026-10-22")
        self.assertEqual(s["ownerMoves"], [{"id": "J4", "date": "2026-10-18", "from": "supported",
                                            "to": "established", "why": "Owner agreed."}])

    def test_releases_summary(self):
        (self.root / "series").mkdir()
        (self.root / "series/releases.json").write_text(json.dumps({"generated": "2026-10-22T19:10:00-07:00", "series": [
            {"id": "fred:A", "status": "ok", "new": [["2026-08", 1.0], ["2026-09", 1.2]], "revised": [["2026-07", 0.9, 0.8]],
             "latest": ["2026-09", 1.2]},
            {"id": "fred:B", "status": "ok", "new": [], "revised": [], "latest": ["2026-09", 3.0]},
            {"id": "bls:C", "status": "stale", "new": [], "revised": [], "latest": None}]}), encoding="utf-8")
        s = state.state(self.root, "2026-10-22")
        # The publisher's release date is not in the series files, so "released" stays null; firstSeen is when our
        # fetch first saw the data (the 2026-10-06 rehearsal's review caught the fetch date labelled as a release date).
        self.assertEqual(s["releases"], [{"series": "fred:A", "period": "2026-09", "released": None, "firstSeen": "2026-10-22",
                                          "value": 1.2, "note": "2 new observations, 1 revised"}])
        self.assertEqual(s["stale"], ["bls:C"])


if __name__ == "__main__":
    unittest.main()
