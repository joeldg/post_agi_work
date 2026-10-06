"""Validator for the Jobs plugin, read-only (spec 7.4). Checks claims.json and every edition in editions/.

    python3 scripts/check_plugin.py [--root DIR] [--rev HEAD]

Prints each problem as "<file>: <where>: <rule>", then CHECK OK (exit 0) or CHECK FAILED: N problem(s) (exit 1).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jobslib import (CLAIM_IDS, DATA_KINDS, DEK_MAX_WORDS, EXTREMES, HEADLINE_MAX, KINDS, LENS_OF,  # noqa: E402
                     MARK_KEYS, QUAL_MAX_WORDS, RATINGS, SERIES_PREFIXES, STATUS, git_ls, git_ok, git_show,
                     load_json, loads_json, steps, url_problem, words)

ROOT = Path(__file__).resolve().parent.parent
EDITION_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
STATUS_RULE = "status must be one of " + ", ".join(STATUS)
SERIES_RULE = "series id must start with " + ", ".join(p + ":" for p in SERIES_PREFIXES[:-1]) + \
              " or " + SERIES_PREFIXES[-1] + ":"


def _series_ok(sid) -> bool:
    if not isinstance(sid, str) or ":" not in sid:
        return False
    prefix, rest = sid.split(":", 1)
    return prefix in SERIES_PREFIXES and bool(rest.strip())


def check_claims(doc: dict) -> list[str]:
    out = []
    p = lambda where, rule: out.append(f"claims.json: {where}: {rule}")  # noqa: E731
    if not isinstance(doc, dict):
        return ["claims.json: top: must be an object"]
    for key in ("version", "changelog", "claims"):
        if key not in doc:
            p("top", f"{key} is required")
    claims = doc.get("claims") or []
    if [c.get("id") for c in claims if isinstance(c, dict)] != CLAIM_IDS:
        p("claims", "claims must be J0 to J12 in order")
    for c in claims:
        if not isinstance(c, dict):
            continue
        cid = c.get("id", "?")
        for key in ("label", "wording"):
            if not str(c.get(key) or "").strip():
                p(cid, f"{key} is required")
        if cid in LENS_OF and c.get("lens") != LENS_OF[cid]:
            p(cid, f"lens must be {LENS_OF[cid]} for {cid}")
        marks = c.get("marks") or {}
        if not all(str(marks.get(k) or "").strip() for k in MARK_KEYS):
            p(cid, "marks need contradicted, emerging, supported and established")
        status = c.get("status")
        if status not in STATUS:
            p(cid, STATUS_RULE)
        inds = c.get("indicators") or []
        if not inds:
            p(cid, "at least one indicator is required")
        for i, ind in enumerate(inds, 1):
            where = f"{cid} indicator {ind.get('id') or i}"
            if not [x for x in (ind.get("confounders") or []) if str(x).strip()]:
                p(where, "indicator needs at least one confounder")
            if ind.get("dataKind") not in DATA_KINDS:
                p(where, "dataKind must be official or private")
            prob = url_problem(ind.get("url"))
            if prob:
                p(where, prob)
            for sid in ind.get("series") or []:
                if not _series_ok(sid):
                    p(where, SERIES_RULE)
        pending = c.get("pending")
        if pending is not None and (not isinstance(pending, dict) or pending.get("to") not in EXTREMES):
            p(cid, "pending.to must be established or contradicted")
        hist = c.get("history") or []
        for n, row in enumerate(hist, 1):
            if n > 1 and row.get("from") != hist[n - 2].get("to"):
                p(cid, f"history row {n}: from must equal the previous row's to")
        if hist and hist[-1].get("to") != status:
            p(cid, "last history row's to must equal status")
    return out


def _edition_ids(doc) -> tuple[set, list]:
    seen, twice = set(), []
    for e in doc.get("evidence") or []:
        eid = e.get("id") if isinstance(e, dict) else None
        if eid in seen and eid not in twice:
            twice.append(eid)
        seen.add(eid)
    return seen, twice


def check_edition(doc: dict, rel: str) -> list[str]:
    out = []
    p = lambda where, rule: out.append(f"{rel}: {where}: {rule}")  # noqa: E731
    if not isinstance(doc, dict):
        return [f"{rel}: top: must be an object"]
    m = EDITION_NAME.match(Path(rel).name)
    if not m or doc.get("date") != m.group(1):
        p("date", "date must match the file name")
    headline = str(doc.get("headline") or "")
    if not headline.strip():
        p("headline", "headline is required")
    elif len(headline) > HEADLINE_MAX:
        p("headline", f"headline is over {HEADLINE_MAX} characters")
    if words(doc.get("dek")) > DEK_MAX_WORDS:
        p("dek", f"dek is over {DEK_MAX_WORDS} words")
    strip = doc.get("strip") or []
    if [s.get("id") for s in strip if isinstance(s, dict)] != CLAIM_IDS:
        p("strip", "strip must list J0 to J12 in order")
    baseline = doc.get("baseline") is True
    for s in strip:
        if not isinstance(s, dict):
            continue
        if s.get("status") not in STATUS:
            p(f"strip {s.get('id')}", STATUS_RULE)
        elif baseline and s.get("status") in EXTREMES:
            p(f"strip {s.get('id')}", f"baseline may not start a claim at {s['status']}")
    ids, twice = _edition_ids(doc)
    for eid in twice:
        p("evidence", f"evidence id {eid} is used twice")

    def refs(where, evs):
        for eid in evs or []:
            if eid not in ids:
                p(where, f"evidence id {eid} is not defined")

    for mv in doc.get("moves") or []:
        where = f"move {mv.get('id')}"
        a, b = mv.get("from"), mv.get("to")
        if a not in STATUS or b not in STATUS:
            p(where, "move from and to must be on the scale")
        elif mv.get("by") != "owner":
            if steps(a, b) > 1:
                p(where, f"move of {steps(a, b)} steps needs by: owner")
            if b in EXTREMES:
                p(where, f"move to {b} needs by: owner")
        refs(where, mv.get("evidence"))
    for pd in doc.get("pendingOwner") or []:
        if pd.get("to") not in EXTREMES:
            p(f"pendingOwner {pd.get('id')}", "pending.to must be established or contradicted")
        refs(f"pendingOwner {pd.get('id')}", pd.get("evidence"))
    for e in doc.get("evidence") or []:
        where = f"evidence {e.get('id')}"
        if e.get("rating") not in RATINGS:
            p(where, "rating must be one of the six ratings")
        if words(e.get("ratingQual")) > QUAL_MAX_WORDS:
            p(where, f"ratingQual is at most {QUAL_MAX_WORDS} words")
        for u in [e.get("url")] + list(e.get("otherUrls") or []):
            prob = url_problem(u)
            if prob:
                p(where, prob)
        if e.get("kind") not in KINDS:
            p(where, "kind must be one of " + ", ".join(KINDS))
        if e.get("dataKind") not in DATA_KINDS + (None,):
            p(where, "dataKind must be official or private")
        bears = e.get("bears") or []
        if not bears:
            p(where, "bears must name at least one claim")
        for b in bears:
            if b.get("claim") not in CLAIM_IDS:
                p(where, f"bears claim {b.get('claim')} is not a claim id")
            if b.get("direction") not in ("for", "against"):
                p(where, "bears direction must be for or against")
    nc = doc.get("nullCase")
    if not isinstance(nc, dict) or not (str(nc.get("none") or "").strip() or str(nc.get("text") or "").strip()):
        p("nullCase", "nullCase is required")
    elif not str(nc.get("none") or "").strip():
        refs("nullCase", nc.get("evidence"))
    for c in doc.get("corrections") or []:
        for key in ("date", "item", "was", "now"):
            if not str(c.get(key) or "").strip():
                p("corrections", f"correction {key} is required")
        prob = url_problem(c.get("url"))
        if prob:
            p("corrections", prob)
    return out


FROZEN_CLAIM_FIELDS = ("label", "wording", "marks", "indicators")
FROZEN_TOP_FIELDS = ("lists", "defaultMarks")


def check_git(root: Path, rev: str, claims: dict | None) -> list[str]:
    """Frozen data against git (spec 4.1, 4.2): committed editions, append-only history, and the claims' wording,
    marks, indicators and lists, which change only with a version bump and a changelog entry."""
    out = []
    for rel in git_ls(root, rev, "editions"):
        if not EDITION_NAME.match(Path(rel).name):
            continue
        path = root / rel
        if not path.exists():
            out.append(f"{rel}: top: {rel} was removed; committed editions are frozen")
        elif path.read_text(encoding="utf-8") != git_show(root, rev, rel):
            out.append(f"{rel}: top: {rel} changed since {rev}; committed editions are frozen")
    head_text = git_show(root, rev, "claims.json")
    if head_text is None or not isinstance(claims, dict):
        return out
    try:
        head = loads_json(head_text)
    except ValueError:
        return out
    now_by_id = {c.get("id"): c for c in claims.get("claims") or [] if isinstance(c, dict)}
    bumped = (claims.get("version") != head.get("version")
              and len(claims.get("changelog") or []) > len(head.get("changelog") or []))
    for hc in head.get("claims") or []:
        cid = hc.get("id")
        nc = now_by_id.get(cid)
        if nc is None:
            continue
        old, new = hc.get("history") or [], nc.get("history") or []
        for n, row in enumerate(old, 1):
            if n > len(new):
                out.append(f"claims.json: {cid}: history row {n} was removed; history is append-only")
                break
            if new[n - 1] != row:
                out.append(f"claims.json: {cid}: history row {n} changed since {rev}; history is append-only")
        if not bumped:
            for field in FROZEN_CLAIM_FIELDS:
                if nc.get(field) != hc.get(field):
                    out.append(f"claims.json: {cid}: {field} changed since {rev} without a version bump and "
                               f"changelog entry")
    if not bumped:
        for field in FROZEN_TOP_FIELDS:
            if claims.get(field) != head.get(field):
                out.append(f"claims.json: top: {field} changed since {rev} without a version bump and changelog entry")
    return out


def check(root: Path, rev: str = "HEAD") -> list[str]:
    root = Path(root)
    out = []
    claims = None
    try:
        claims = load_json(root / "claims.json")
    except (OSError, ValueError) as e:
        out.append(f"claims.json: top: does not parse ({e})")
    if claims is not None:
        out += check_claims(claims)
    for path in sorted((root / "editions").glob("*.json")):
        rel = f"editions/{path.name}"
        try:
            doc = load_json(path)
        except (OSError, ValueError) as e:
            out.append(f"{rel}: top: does not parse ({e})")
            continue
        out += check_edition(doc, rel)
    if git_ok(root, rev):
        out += check_git(root, rev, claims)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate claims.json and the editions (read-only).")
    ap.add_argument("--root", default=str(ROOT), help="plugin repo root")
    ap.add_argument("--rev", default="HEAD", help="git revision the frozen checks compare against")
    a = ap.parse_args(argv)
    problems = check(Path(a.root), a.rev)
    if not git_ok(Path(a.root), a.rev):
        print(f"note: no git at {a.rev}; frozen checks skipped")
    for line in problems:
        print(line)
    print("CHECK OK" if not problems else f"CHECK FAILED: {len(problems)} problem(s)")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
