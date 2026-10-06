"""Constants and helpers shared by the Jobs plugin's scripts (spec 4 and 6).

Stored status values are ids; display words are separate (STATUS_LABEL). Python 3.9+, standard library only.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

CLAIM_IDS = [f"J{i}" for i in range(13)]
STATUS = ["contradicted", "no-clear-sign", "emerging", "supported", "established"]
STATUS_LABEL = {"contradicted": "Contradicted", "no-clear-sign": "No clear sign", "emerging": "Emerging",
                "supported": "Supported", "established": "Established"}
EXTREMES = frozenset({"contradicted", "established"})
MARK_KEYS = ("contradicted", "emerging", "supported", "established")
RATINGS = ("verified fact", "credible report", "expert opinion", "forecast aggregate", "our inference", "speculation")
KINDS = ("official-series", "filing", "company-statement", "research", "press", "court", "regulator", "market-data")
DATA_KINDS = ("official", "private")
LENSES = {"capital": ["J1", "J8", "J9"], "work": ["J2", "J3", "J6"], "prices": ["J5", "J10"],
          "buyers": ["J4", "J11"], "policy": ["J7", "J12"], "null": ["J0"]}
LENS_OF = {cid: lens for lens, ids in LENSES.items() for cid in ids}
# The newsletter's aggregator denylist (scripts/check_data.py DENYLIST); the newsletter's import enforces its own copy.
DENYLIST = ("shattered.io", "aitoolsreview.co.uk", "geotoolbox.ai", "aistop.watch", "aiweekly.co")
SERIES_PREFIXES = ("fred", "bls", "stooq", "basket")
HEADLINE_MAX = 90
DEK_MAX_WORDS = 60
QUAL_MAX_WORDS = 5
WORD = re.compile(r"\S+")


def steps(a: str, b: str) -> int:
    """How many steps apart two statuses are on the scale."""
    return abs(STATUS.index(a) - STATUS.index(b))


def words(s) -> int:
    return len(WORD.findall(s)) if isinstance(s, str) else 0


def _no_duplicates(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate key {k!r}")
        out[k] = v
    return out


def _no_constant(name):
    raise ValueError(f"{name} is not valid JSON")


def loads_json(text: str):
    """json.loads that refuses duplicate keys and NaN/Infinity, which plain json silently accepts."""
    return json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)


def load_json(path: Path):
    return loads_json(Path(path).read_text(encoding="utf-8"))


def dump_json(doc) -> str:
    """The house style: indent 1, UTF-8 kept, trailing newline."""
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def url_problem(u) -> str | None:
    if not isinstance(u, str):
        return "url must be http(s)"
    parts = urlsplit(u.strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return "url must be http(s)"
    host = (parts.hostname or "").lower()
    for d in DENYLIST:
        if host == d or host.endswith("." + d):
            return f"url is on the denylist ({d})"
    return None


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def git_ok(root: Path, rev: str) -> bool:
    r = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "--quiet", rev + "^{commit}"],
                       capture_output=True, text=True)
    return r.returncode == 0


def git_show(root: Path, rev: str, rel: str) -> str | None:
    """A file's text at a revision, or None when it isn't there."""
    r = subprocess.run(["git", "-C", str(root), "show", f"{rev}:{rel}"], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def git_ls(root: Path, rev: str, folder: str) -> list:
    """File paths under a folder at a revision."""
    r = subprocess.run(["git", "-C", str(root), "ls-tree", "-r", "--name-only", rev, "--", folder],
                       capture_output=True, text=True)
    return [line for line in r.stdout.splitlines() if line] if r.returncode == 0 else []
