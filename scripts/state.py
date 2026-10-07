"""What a run starts from, read by code so the workflow never has to guess (spec 7.2).

    python3 scripts/state.py --date YYYY-MM-DD [--root DIR]

Prints JSON: claimsVersion; prev (the newest edition dated before DATE, with its strip, or null); claims (each one's
id, label, current status and pending move); ownerMoves (moves the owner confirmed since prev); releases (series with
new observations, from series/releases.json); stale (series that failed to fetch).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jobslib import load_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


def state(root: Path, date: str) -> dict:
    root = Path(root)
    claims = load_json(root / "claims.json")
    earlier = sorted(p for p in (root / "editions").glob("*.json") if p.stem < date) if (root / "editions").exists() else []
    prev = None
    if earlier:
        doc = load_json(earlier[-1])
        prev = {"date": doc.get("date"), "strip": doc.get("strip") or []}
    since = prev["date"] if prev else ""
    owner_moves = []
    for c in claims.get("claims") or []:
        for row in c.get("history") or []:
            if row.get("by") == "owner" and row.get("from") != row.get("to") and since < row.get("date", "") <= date:
                owner_moves.append({"id": c["id"], "date": row["date"], "from": row["from"], "to": row["to"],
                                    "why": row.get("why", "")})
    releases, stale = [], []
    rel_path = root / "series" / "releases.json"
    if rel_path.exists():
        rel = load_json(rel_path)
        seen = str(rel.get("generated") or "")[:10]
        for s in rel.get("series") or []:
            if s.get("status") != "ok":
                stale.append(s.get("id"))
                continue
            if not s.get("new"):
                continue
            last = s["new"][-1]
            note = _plural(len(s["new"]), "new observation")
            if s.get("revised"):
                note += f", {len(s['revised'])} revised"
            releases.append({"series": s["id"], "period": last[0], "released": None, "firstSeen": seen, "value": last[1],
                             "note": note})
    return {
        "date": date,
        "claimsVersion": claims.get("version"),
        "prev": prev,
        "claims": [{"id": c.get("id"), "label": c.get("label"), "status": c.get("status"), "pending": c.get("pending")}
                   for c in claims.get("claims") or []],
        "ownerMoves": owner_moves,
        "releases": releases,
        "stale": stale,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Print the state a run starts from, as JSON.")
    ap.add_argument("--date", required=True, help="the run's date, YYYY-MM-DD")
    ap.add_argument("--root", default=str(ROOT), help="plugin repo root")
    a = ap.parse_args(argv)
    print(json.dumps(state(Path(a.root), a.date), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
