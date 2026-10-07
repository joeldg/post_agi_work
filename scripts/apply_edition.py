"""Write one run's edition and its claims.json update, then validate (the jobs-weekly workflow's Write stage).

    python3 scripts/apply_edition.py PAYLOAD.json [--root DIR]

PAYLOAD is {"edition": {...spec 4.2...}, "claims": [{"id", "status"?, "since"?, "pending"?, "history"?}], "checksum"}.
The checksum (jobslib.payload_checksum over edition and claims) must match, or nothing is written. Each claims
entry may set only status, since and pending, and append one history row; anything else is refused, because a run
never changes a claim's wording, marks, indicators or lists (spec 4.1). An edition already committed is refused (it is
frozen); an uncommitted one from an earlier attempt today is overwritten, and the claims patch is applied to
claims.json as committed, so a rerun replaces the earlier attempt rather than adding to it. Prints check_plugin's problems, then
CHECK OK (exit 0) or CHECK FAILED (exit 1); a refused payload exits 2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_plugin  # noqa: E402
from jobslib import dump_json, git_ok, git_show, load_json, loads_json, payload_checksum  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PATCH_KEYS = {"id", "status", "since", "pending", "history"}


def apply(root: Path, payload: dict) -> list[str]:
    root = Path(root)
    ed = payload.get("edition")
    if not isinstance(ed, dict) or not isinstance(ed.get("date"), str):
        raise ValueError("payload.edition with a date is required")
    rel = f"editions/{ed['date']}.json"
    if git_ok(root, "HEAD") and git_show(root, "HEAD", rel) is not None:
        raise ValueError(f"{rel} is already committed; committed editions are frozen")
    # Patch claims.json as committed, never an earlier attempt's working copy: a rerun then replaces the first attempt
    # instead of stacking a second step on it (the 2026-10-06 review's I2).
    head = git_show(root, "HEAD", "claims.json") if git_ok(root, "HEAD") else None
    claims = loads_json(head) if head is not None else load_json(root / "claims.json")
    by_id = {c["id"]: c for c in claims["claims"]}
    for patch in payload.get("claims") or []:
        cid = patch.get("id")
        if cid not in by_id:
            raise ValueError(f"{cid} is not a claim")
        for key in patch:
            if key not in PATCH_KEYS:
                raise ValueError(f"{cid}: a run may not set {key}")
    for patch in payload.get("claims") or []:
        c = by_id[patch["id"]]
        for key in ("status", "since", "pending"):
            if key in patch:
                c[key] = patch[key]
        if patch.get("history"):
            c["history"] = list(c.get("history") or []) + [patch["history"]]
    (root / "editions").mkdir(exist_ok=True)
    (root / rel).write_text(dump_json(ed), encoding="utf-8")
    (root / "claims.json").write_text(dump_json(claims), encoding="utf-8")
    return check_plugin.check(root)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write a run's edition and claims update, then validate.")
    ap.add_argument("payload", help="path to the payload JSON")
    ap.add_argument("--root", default=str(ROOT), help="plugin repo root")
    a = ap.parse_args(argv)
    try:
        payload = load_json(Path(a.payload))
        want = payload.get("checksum")
        if not want:
            raise ValueError("the payload has no checksum; the workflow always signs it")
        if payload_checksum({"edition": payload.get("edition"), "claims": payload.get("claims")}) != want:
            raise ValueError("payload checksum mismatch: the payload changed between the workflow and the disk")
        problems = apply(Path(a.root), payload)
    except (OSError, ValueError, TypeError) as e:
        print(f"apply_edition: {e}")
        return 2
    for line in problems:
        print(line)
    print("CHECK OK" if not problems else f"CHECK FAILED: {len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
