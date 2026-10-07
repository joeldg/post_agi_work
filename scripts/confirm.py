"""The owner's decision on a pending move to Established or Contradicted (spec 5.2 rule 2, 7.5).

    python3 scripts/confirm.py J4 --to established
    python3 scripts/confirm.py J4 --reject

Confirming applies the pending move with a history row by the owner; rejecting clears it with a history row that
keeps the status. Either way claims.json is committed locally (never pushed), so Thursday's clean-tree check passes;
the next run pushes the commit and reports the decision. Exit 0, or 2 with the reason on stderr.
"""
from __future__ import annotations

import argparse
import copy
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_plugin  # noqa: E402
from jobslib import CLAIM_IDS, EXTREMES, dump_json, load_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def apply(doc: dict, claim: str, to: str | None, reject: bool, today: str) -> tuple[dict, str]:
    """The claims document with the owner's decision applied, and the commit message. The input is not changed."""
    if claim not in CLAIM_IDS:
        raise ValueError(f"{claim} is not a claim")
    if not reject and to not in EXTREMES:
        raise ValueError("--to must be established or contradicted")
    doc = copy.deepcopy(doc)
    c = next((x for x in doc.get("claims") or [] if x.get("id") == claim), None)
    if c is None:
        raise ValueError(f"{claim} is not in claims.json")
    pending = c.get("pending")
    if not pending:
        raise ValueError(f"{claim} has no pending move")
    if not reject and pending.get("to") != to:
        raise ValueError(f"{claim}'s pending move is to {pending.get('to')}, not {to}")
    status = c["status"]
    if reject:
        row = {"date": today, "from": status, "to": status, "why": f"The owner rejected the move to {pending['to']}.",
               "evidence": list(pending.get("evidence") or []), "by": "owner", "note": f"rejected: {pending['to']}"}
        msg = f"Owner rejects {claim}: {pending['to']}"
    else:
        row = {"date": today, "from": status, "to": to, "why": pending.get("why", ""),
               "evidence": list(pending.get("evidence") or []), "by": "owner"}
        c["status"], c["since"] = to, today
        msg = f"Owner confirms {claim}: {to}"
    c["history"] = list(c.get("history") or []) + [row]
    c["pending"] = None
    return doc, msg


def pacific_today() -> str:
    env = dict(os.environ, TZ="America/Los_Angeles")
    r = subprocess.run(["date", "+%F"], capture_output=True, text=True, env=env)
    return r.stdout.strip() or datetime.now().strftime("%Y-%m-%d")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Confirm or reject a pending move to Established or Contradicted.")
    ap.add_argument("claim", help="claim id, e.g. J4")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--to", choices=sorted(EXTREMES), help="confirm the pending move to this status")
    g.add_argument("--reject", action="store_true", help="reject the pending move; the status stays")
    ap.add_argument("--root", default=str(ROOT), help="plugin repo root")
    ap.add_argument("--today", help="the decision date (default: today, Pacific)")
    a = ap.parse_args(argv)
    root = Path(a.root)
    path = root / "claims.json"
    git = lambda *args: subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)  # noqa: E731
    # Only the owner's decision goes into this commit: never a failed run's leftovers or anything else staged
    # (the 2026-10-06 review's I1).
    if git("diff", "--quiet", "HEAD", "--", "claims.json").returncode != 0:
        print("confirm: claims.json has uncommitted changes; restore it (git checkout -- claims.json) or let the "
              "Thursday run finish first", file=sys.stderr)
        return 2
    if git("diff", "--cached", "--quiet").returncode != 0:
        print("confirm: there are staged changes; unstage them first (git reset)", file=sys.stderr)
        return 2
    try:
        doc, msg = apply(load_json(path), a.claim, a.to, a.reject, a.today or pacific_today())
    except (OSError, ValueError) as e:
        print(f"confirm: {e}", file=sys.stderr)
        return 2
    original = path.read_text(encoding="utf-8")
    path.write_text(dump_json(doc), encoding="utf-8")
    problems = check_plugin.check(root)
    if problems:
        path.write_text(original, encoding="utf-8")
        print("confirm: the result fails check_plugin, so nothing was written:\n" + "\n".join(problems), file=sys.stderr)
        return 2
    done = git("commit", "-q", "-m", msg, "--", "claims.json")
    if done.returncode != 0:
        path.write_text(original, encoding="utf-8")
        print(f"confirm: git commit failed: {done.stderr.strip()}", file=sys.stderr)
        return 2
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
