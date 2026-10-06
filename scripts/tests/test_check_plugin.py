"""Tests for scripts/check_plugin.py and scripts/jobslib.py. Stdlib unittest, no network:

    python3 -m unittest discover -s scripts/tests -t .

fixtures/base/ is a valid plugin tree: claims.json (J0-J12; J3 moved to Emerging on 2026-10-15; J4 Supported with a
pending move to Established) and two editions (the 2026-10-08 baseline and the 2026-10-15 edition). Each
fixtures/cases/*.json breaks one rule: `head_ops` edit the tree before it is committed (default: the base as is),
`ops` edit the working tree after the commit, and `expect` is part of the problem the rule must print.
"""
import contextlib
import copy
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent
sys.path.insert(0, str(SCRIPTS))

import check_plugin  # noqa: E402
import jobslib  # noqa: E402

FIX = HERE / "fixtures"
BASE = FIX / "base"
CASES = FIX / "cases"


def apply_ops(root, ops):
    for op in ops or []:
        path = root / op["file"]
        if op.get("remove"):
            path.unlink()
            continue
        if "write" in op:
            path.parent.mkdir(parents=True, exist_ok=True)
            text = op["write"] if isinstance(op["write"], str) else json.dumps(op["write"], indent=1) + "\n"
            path.write_text(text, encoding="utf-8")
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        keys = op.get("set") or op.get("del") or op.get("append")
        cur = doc
        for k in keys[:-1]:
            cur = cur[k]
        if "set" in op:
            cur[keys[-1]] = copy.deepcopy(op["value"])
        elif "del" in op:
            del cur[keys[-1]]
        else:
            cur[keys[-1]].append(copy.deepcopy(op["value"]))
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def make_repo(head_ops=None):
    """A temp git repo holding the base tree (after head_ops), committed. The caller removes it."""
    root = Path(tempfile.mkdtemp(prefix="jobs-check-"))
    shutil.copytree(BASE, root, dirs_exist_ok=True)
    apply_ops(root, head_ops)
    git(root, "init", "-q")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
    git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
    return root


def run_case(case):
    root = make_repo((case or {}).get("head_ops"))
    try:
        apply_ops(root, (case or {}).get("ops"))
        return check_plugin.check(root)
    finally:
        shutil.rmtree(root, ignore_errors=True)


class Base(unittest.TestCase):
    def test_base_passes(self):
        self.assertEqual(run_case(None), [])

    def test_duplicate_key_refused(self):
        with self.assertRaises(ValueError):
            jobslib.loads_json('{"a": 1, "a": 2}')

    def test_nan_refused(self):
        with self.assertRaises(ValueError):
            jobslib.loads_json('{"a": NaN}')

    def test_steps(self):
        self.assertEqual(jobslib.steps("no-clear-sign", "supported"), 2)
        self.assertEqual(jobslib.steps("contradicted", "no-clear-sign"), 1)

    def test_url_problem(self):
        self.assertIsNone(jobslib.url_problem("https://www.bls.gov/jlt/"))
        self.assertEqual(jobslib.url_problem("https://news.aiweekly.co/x"), "url is on the denylist (aiweekly.co)")
        self.assertEqual(jobslib.url_problem("javascript:alert(1)"), "url must be http(s)")

    def test_main_exit_codes(self):
        root = make_repo()
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(check_plugin.main(["--root", str(root)]), 0)
            self.assertIn("CHECK OK", out.getvalue())
            apply_ops(root, [{"file": "claims.json", "set": ["claims", 0, "status"], "value": "likely"}])
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(check_plugin.main(["--root", str(root)]), 1)
            self.assertIn("CHECK FAILED", out.getvalue())
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_unreadable_json_is_a_problem_not_a_crash(self):
        problems = run_case({"ops": [{"file": "editions/2026-10-15.json", "write": "{not json"}]})
        self.assertTrue(any(p.startswith("editions/2026-10-15.json:") and "does not parse" in p for p in problems), problems)


class Frozen(unittest.TestCase):
    def test_version_bump_allows_wording_change(self):
        ops = [{"file": "claims.json", "set": ["claims", 1, "wording"], "value": "New wording."},
               {"file": "claims.json", "set": ["version"], "value": "1.1"},
               {"file": "claims.json", "append": ["changelog"],
                "value": {"version": "1.1", "date": "2026-10-20", "note": "Reworded J1."}}]
        self.assertEqual(run_case({"ops": ops}), [])

    def test_new_edition_is_not_frozen(self):
        doc = json.loads((BASE / "editions/2026-10-15.json").read_text(encoding="utf-8"))
        doc["date"] = "2026-10-22"
        doc["window"] = {"from": "2026-10-16", "to": "2026-10-22"}
        self.assertEqual(run_case({"ops": [{"file": "editions/2026-10-22.json", "write": doc}]}), [])

    def test_history_appended_row_is_allowed(self):
        row = {"date": "2026-10-22", "from": "emerging", "to": "supported", "why": "Two kinds agree.",
               "evidence": ["2026-10-22#e1"], "by": "run"}
        ops = [{"file": "claims.json", "append": ["claims", 3, "history"], "value": row},
               {"file": "claims.json", "set": ["claims", 3, "status"], "value": "supported"}]
        self.assertEqual(run_case({"ops": ops}), [])


class Cases(unittest.TestCase):
    def test_every_case_fails_with_its_message(self):
        paths = sorted(CASES.glob("*.json"))
        self.assertTrue(paths)
        for path in paths:
            case = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(case=path.stem):
                problems = run_case(case)
                self.assertTrue(any(case["expect"] in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
