"""Tests for scripts/confirm.py (spec 7.5). Stdlib unittest, no network."""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import check_plugin  # noqa: E402
import confirm  # noqa: E402
from scripts.tests.test_check_plugin import BASE, make_repo  # noqa: E402

PENDING_WHY = "Two quarters of official data."


def claims():
    return json.loads((BASE / "claims.json").read_text(encoding="utf-8"))


def by_id(doc, cid):
    return next(c for c in doc["claims"] if c["id"] == cid)


class Apply(unittest.TestCase):
    def test_confirm_applies_pending_with_owner_row(self):
        doc, msg = confirm.apply(claims(), "J4", "established", False, "2026-10-20")
        j4 = by_id(doc, "J4")
        self.assertEqual((j4["status"], j4["since"], j4["pending"]), ("established", "2026-10-20", None))
        self.assertEqual(j4["history"][-1], {"date": "2026-10-20", "from": "supported", "to": "established",
                                             "why": PENDING_WHY, "evidence": ["2026-10-15#e2"], "by": "owner"})
        self.assertEqual(msg, "Owner confirms J4: established")

    def test_reject_keeps_status_and_notes_it(self):
        doc, msg = confirm.apply(claims(), "J4", None, True, "2026-10-20")
        j4 = by_id(doc, "J4")
        self.assertEqual((j4["status"], j4["pending"]), ("supported", None))
        last = j4["history"][-1]
        self.assertEqual((last["from"], last["to"], last["note"], last["by"]),
                         ("supported", "supported", "rejected: established", "owner"))
        self.assertEqual(msg, "Owner rejects J4: established")

    def test_refuses_without_pending(self):
        with self.assertRaisesRegex(ValueError, "J3 has no pending move"):
            confirm.apply(claims(), "J3", "established", False, "2026-10-20")

    def test_refuses_wrong_target(self):
        with self.assertRaisesRegex(ValueError, "J4's pending move is to established, not contradicted"):
            confirm.apply(claims(), "J4", "contradicted", False, "2026-10-20")

    def test_refuses_unknown_claim(self):
        with self.assertRaisesRegex(ValueError, "J13 is not a claim"):
            confirm.apply(claims(), "J13", "established", False, "2026-10-20")

    def test_input_is_not_mutated(self):
        doc = claims()
        confirm.apply(doc, "J4", "established", False, "2026-10-20")
        self.assertEqual(by_id(doc, "J4")["status"], "supported")


class Main(unittest.TestCase):
    def test_result_passes_check_plugin_and_is_committed(self):
        root = make_repo()
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                code = confirm.main(["J4", "--to", "established", "--root", str(root), "--today", "2026-10-20"])
            self.assertEqual(code, 0)
            self.assertEqual(check_plugin.check(root), [])
            status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
            self.assertEqual(status.stdout, "")
            log = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%s"], capture_output=True, text=True)
            self.assertEqual(log.stdout.strip(), "Owner confirms J4: established")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_refusal_exits_2_and_writes_nothing(self):
        root = make_repo()
        try:
            with contextlib.redirect_stderr(io.StringIO()) as err:
                code = confirm.main(["J3", "--to", "established", "--root", str(root), "--today", "2026-10-20"])
            self.assertEqual(code, 2)
            self.assertIn("J3 has no pending move", err.getvalue())
            status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
            self.assertEqual(status.stdout, "")
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
