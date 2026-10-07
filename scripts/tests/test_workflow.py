"""Tests for the plain-code paths of .claude/workflows/jobs-weekly.js, run under Node with stubbed agents
(workflow_harness.mjs). Skipped when node is not installed, so the suite stays stdlib-only.

Each scenario is a small ES module that imports the harness, runs the workflow with scripted agent replies and prints
{out, payload, logs} as JSON.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")


def run(body):
    """Run a scenario body (JS using run, baseState, stdResponders, decision) and return its printed JSON."""
    src = ("import { run, baseState, stdResponders, decision } from " + json.dumps((HERE / "workflow_harness.mjs").as_uri())
           + ";\n" + body + "\nconsole.log(JSON.stringify(r))\n")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False) as f:
        f.write(src)
        path = f.name
    try:
        res = subprocess.run([NODE, path], capture_output=True, text=True, timeout=60)
    finally:
        Path(path).unlink()
    if res.returncode != 0:
        raise AssertionError(res.stderr[-2000:])
    return json.loads(res.stdout.strip().splitlines()[-1])


@unittest.skipUnless(NODE, "node is not installed")
class Ready(unittest.TestCase):
    def test_null_review_is_never_ready(self):
        r = run("const r = await run({date: '2026-10-15'}, stdResponders(baseState(), {decision: decision(), review: undefined}))")
        self.assertFalse(r["out"]["ready"])
        self.assertIn("review", r["out"]["reason"])

    def test_check_failure_fixed_by_the_fixer_is_ready(self):
        r = run("const r = await run({date: '2026-10-15'}, stdResponders(baseState(), {decision: decision(), "
                "write: {exitCode: 1, output: 'CHECK FAILED: 1 problem(s)'}, review: {problems: []}, fix: {ok: true, checkOutput: 'CHECK OK'}}))")
        self.assertTrue(r["out"]["ready"], r["out"])

    def test_refused_payload_is_never_ready(self):
        r = run("const r = await run({date: '2026-10-15'}, stdResponders(baseState(), {decision: decision(), "
                "write: {exitCode: 2, output: 'apply_edition: refused'}, review: {problems: []}, fix: {ok: true, checkOutput: 'CHECK OK'}}))")
        self.assertFalse(r["out"]["ready"])

    def test_unfixed_problems_are_never_ready(self):
        r = run("const r = await run({date: '2026-10-15'}, stdResponders(baseState(), {decision: decision(), "
                "review: {problems: [{where: 'dek', problem: 'p', fix: 'f', severity: 'must'}]}, fix: undefined}))")
        self.assertFalse(r["out"]["ready"])
        self.assertIn("fix", r["out"]["reason"])


@unittest.skipUnless(NODE, "node is not installed")
class FailedLens(unittest.TestCase):
    def test_a_failed_lens_is_named_and_its_claims_hold(self):
        body = ("const st = baseState(); st.claims[1].status = 'emerging'; st.prev.strip[1].status = 'emerging';\n"
                "const r = await run({date: '2026-10-15'}, stdResponders(st, {researchFail: {capital: new Error('boom')}, "
                "decision: decision({J1: {status: 'no-clear-sign', why: 'moved without evidence'}})}))")
        r = run(body)
        gaps = " ".join(r["payload"]["edition"]["gaps"])
        self.assertIn("Capital lens failed", gaps)
        self.assertNotIn("lens ?", gaps)
        self.assertEqual([p for p in r["payload"]["claims"] if p["id"] == "J1"], [])
        j1 = next(s for s in r["payload"]["edition"]["strip"] if s["id"] == "J1")
        self.assertEqual(j1["status"], "emerging")


@unittest.skipUnless(NODE, "node is not installed")
class Headline(unittest.TestCase):
    def test_a_failed_headline_rewrite_never_keeps_the_stale_headline(self):
        body = ("const r = await run({date: '2026-10-15'}, stdResponders(baseState(), {"
                "decision: decision({J3: {status: 'emerging', evidence: ['e7']}}, {headline: 'J3 reaches Emerging'}), "
                "moveCheck: {J3: {id: 'J3', holds: false, status: 'no-clear-sign', pendingHolds: false, why: 'notes', publishedWhy: 'We hold No clear sign.'}}, "
                "headline: undefined}))")
        r = run(body)
        self.assertNotEqual(r["payload"]["edition"]["headline"], "J3 reaches Emerging")


@unittest.skipUnless(NODE, "node is not installed")
class Statuses(unittest.TestCase):
    def test_an_extreme_is_proposed_never_applied(self):
        body = ("const st = baseState(); st.claims[4].status = 'supported'; st.prev.strip[4].status = 'supported';\n"
                "const r = await run({date: '2026-10-15'}, stdResponders(st, {decision: decision({J4: {status: 'established', evidence: ['e1']}}), "
                "moveCheck: {J4: {id: 'J4', holds: true, status: 'established', pendingHolds: true, why: 'n', publishedWhy: ''}}}))")
        r = run(body)
        j4 = next(s for s in r["payload"]["edition"]["strip"] if s["id"] == "J4")
        self.assertEqual((j4["status"], j4["pending"]), ("supported", {"to": "established"}))
        self.assertEqual([x["id"] for x in r["payload"]["edition"]["pendingOwner"]], ["J4"])

    def test_owner_moves_are_reported(self):
        body = ("const st = baseState({ownerMoves: [{id: 'J4', date: '2026-10-06', from: 'supported', to: 'established', why: 'Owner agreed.'}]});\n"
                "st.claims[4].status = 'established';\n"
                "const r = await run({date: '2026-10-15'}, stdResponders(st, {decision: decision({J4: {status: 'established'}})}))")
        r = run(body)
        self.assertIn({"id": "J4", "from": "supported", "to": "established", "by": "owner"},
                      [{k: m[k] for k in ("id", "from", "to", "by")} for m in r["payload"]["edition"]["moves"]])


@unittest.skipUnless(NODE, "node is not installed")
class Checksum(unittest.TestCase):
    def test_js_and_python_checksums_agree(self):
        import sys
        sys.path.insert(0, str(HERE.parent))
        import jobslib
        from scripts.tests.test_apply_edition import payload
        pl = payload()
        doc = {"edition": pl["edition"], "claims": pl["claims"]}
        doc["edition"]["evidence"][0]["text"] = "Grün, naïve – 2.5% “quoted” 😀 and 1e-7 small."
        doc["edition"]["releases"] = [{"series": "fred:X", "value": 93.446, "n": 3, "z": None, "t": True}]
        src = (HERE.parent.parent / ".claude/workflows/jobs-weekly.js").read_text(encoding="utf-8")
        fn = src[src.index("// checksum:begin"):src.index("// checksum:end")]
        js = fn + "\nconst d = JSON.parse(require('fs').readFileSync(0, 'utf8'));\nconsole.log(payloadChecksum(d))\n"
        res = subprocess.run([NODE, "-e", js], input=json.dumps(doc), capture_output=True, text=True, timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), jobslib.payload_checksum(doc))


if __name__ == "__main__":
    unittest.main()
