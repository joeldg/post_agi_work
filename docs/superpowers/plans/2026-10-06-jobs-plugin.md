# Jobs plugin (post_agi_work) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Jobs plugin repo (claims, scripts, the Thursday workflow and routine text) and produce, commit and push the baseline edition.

**Architecture:** A standalone repo. `claims.json` holds the thirteen claims; `fetch_series.py` pulls official and market series; the `jobs-weekly` workflow researches, verifies, decides and writes one edition per run; `check_plugin.py` enforces the data contract and the frozen-data rules against git; `confirm.py` applies the owner's decision on a pending extreme. The newsletter side is a separate plan (`2026-10-06-jobs-newsletter-integration.md`).

**Tech Stack:** Python 3.9+ standard library only; git; the Claude Code Workflow tool (JavaScript workflow script); FRED, BLS and Stooq public endpoints.

**Spec:** `docs/superpowers/specs/2026-10-06-jobs-plugin-design.md`

## Global Constraints

- Python 3.9 or newer, standard library only; use `from __future__ import annotations` for `X | None` hints. JSON is written with `json.dumps(doc, indent=1, ensure_ascii=False) + "\n"` (the newsletter's house style).
- Tests: `python3 -m unittest discover -s scripts/tests -t .` from the repo root; no network in tests.
- Claim ids: `J0` … `J12`, in that order.
- Status ids, in order 0-4: `contradicted`, `no-clear-sign`, `emerging`, `supported`, `established`. Labels: Contradicted, No clear sign, Emerging, Supported, Established. Extremes: `contradicted`, `established`.
- Ratings (closed set): `verified fact`, `credible report`, `expert opinion`, `forecast aggregate`, `our inference`, `speculation`.
- Evidence `kind`: `official-series`, `filing`, `company-statement`, `research`, `press`, `court`, `regulator`, `market-data`. `dataKind`: `official`, `private`.
- Lenses: `capital` J1 J8 J9 · `work` J2 J3 J6 · `prices` J5 J10 · `buyers` J4 J11 · `policy` J7 J12 · `null` J0.
- Limits: `headline` ≤ 90 characters; `dek` ≤ 60 words; `ratingQual` ≤ 5 words.
- Denylist (from the newsletter's `scripts/check_data.py`): `shattered.io`, `aitoolsreview.co.uk`, `geotoolbox.ai`, `aistop.watch`, `aiweekly.co`.
- Series id prefixes: `fred:`, `bls:`, `stooq:`, `basket:`.
- Workflow agents: model `fable`, effort `max`; a null or thrown result retries once with no model override at effort `max`, label logged in `fallbacks`.
- Commits name explicit paths; never `git add -A` or `git add .`; never force-push. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- No investment language anywhere (no buy, sell, hold, price targets). Voice: first person plural; the author is "a custom AI agent".

## Review Focus

1. A series endpoint answers with an HTML error or captcha page instead of data: the last good file must survive and the series must read `stale` (Task 4, `test_html_body_keeps_last_good`).
2. BLS's keyless API refuses a request (`status` other than `REQUEST_SUCCEEDED`, e.g. the daily limit): `stale`, never a crash (Task 4, `test_bls_refusal_is_stale`).
3. Two evidence items share an id, so a move's evidence is ambiguous: the check must fail (Task 1, case `evidence_id_twice`).
4. A JSON file with a duplicate key silently loses data on load: loading must refuse it (Task 1, `test_duplicate_key_refused`).
5. A run rewords a claim or edits its marks without a version bump: the frozen check must catch it (Task 2, case `wording_changed_no_bump`).

## File Structure

```
.gitignore, LICENSE, LICENSE-content.md, README.md        Task 1 (README completed in Task 7)
scripts/jobslib.py            constants and helpers shared by every script                    Task 1
scripts/check_plugin.py       the validator: claims, editions, git frozen rules               Tasks 1-2
scripts/confirm.py            owner confirms or rejects a pending extreme                     Task 3
scripts/fetch_series.py       series fetcher, basket derivation, releases.json                Task 4
scripts/tests/                test_check_plugin.py, test_confirm.py, test_fetch_series.py, fixtures/
claims.json                   v1.0 content                                                    Task 5
series/                       written by fetch_series.py                                      Task 5
.claude/workflows/jobs-weekly.js   the Thursday workflow                                      Task 6
docs/routine.md               the scheduled task's instructions                               Task 7
editions/<date>.json          the baseline                                                    Task 8
```

---

### Task 1: Scaffold, shared library and the data-contract checks

**Files:**
- Create: `.gitignore`, `LICENSE`, `LICENSE-content.md`, `README.md` (a stub: one paragraph and "see docs/superpowers/specs/"), `scripts/jobslib.py`, `scripts/check_plugin.py`, `scripts/tests/__init__.py`, `scripts/tests/test_check_plugin.py`, `scripts/tests/fixtures/base/claims.json`, `scripts/tests/fixtures/base/editions/2026-10-08.json`, `scripts/tests/fixtures/base/editions/2026-10-15.json`, `scripts/tests/fixtures/cases/*.json`

**Interfaces:**
- Produces (`jobslib.py`): `CLAIM_IDS: list[str]`, `STATUS: list[str]` (in order), `STATUS_LABEL: dict[str, str]`, `EXTREMES: frozenset`, `RATINGS: tuple`, `KINDS: tuple`, `DATA_KINDS: tuple`, `LENSES: dict[str, list[str]]`, `DENYLIST: tuple`, `SERIES_PREFIXES: tuple`, `HEADLINE_MAX = 90`, `DEK_MAX_WORDS = 60`, `QUAL_MAX_WORDS = 5`, `steps(a: str, b: str) -> int` (absolute order difference), `words(s: str) -> int`, `load_json(path: Path) -> object` (raises `ValueError` on a duplicate key or NaN), `loads_json(text: str) -> object` (same rules), `dump_json(doc) -> str`, `url_problem(u: str) -> str | None`, `git_show(root: Path, rev: str, rel: str) -> str | None`, `git_ok(root: Path, rev: str) -> bool`.
- Produces (`check_plugin.py`): `check(root: Path, rev: str = "HEAD") -> list[str]` (problems as `"<file>: <where>: <rule>"`), `check_claims(doc: dict) -> list[str]`, `check_edition(doc: dict, rel: str) -> list[str]`, `main(argv: list[str] | None = None) -> int` (prints each problem, then `CHECK OK` or `CHECK FAILED: N problem(s)`; exit 0 or 1).

- [ ] **Step 1: Write the scaffold files.** `.gitignore`: `.claude/work/`, `__pycache__/`, `.DS_Store`. `LICENSE`: MIT, "Copyright (c) 2026 joeldg". `LICENSE-content.md`: copy the newsletter's `LICENSE-content.md` (`/Users/joeldg/Projects/agi_assessment-redesign/LICENSE-content.md`) adapted to name this repo's `claims.json`, `editions/` and `series/` (series data stays under its publishers' terms).

- [ ] **Step 2: Write the fixtures.** `base/claims.json`: a valid v1.0 file with all thirteen claims (short wording, one indicator each with one confounder, marks for the four non-default statuses, `lens` matching `LENSES`), `lists: {}`, J3 at `emerging` with a two-row history (`null→no-clear-sign` 2026-10-08, `no-clear-sign→emerging` 2026-10-15), every other claim with one baseline row (`from: null`), J4 at `supported` with `pending: {"to": "established", "since": "2026-10-15", "why": "…", "evidence": ["2026-10-15#e2"]}`. `base/editions/2026-10-08.json`: `baseline: true`, `prev` all null, no moves. `base/editions/2026-10-15.json`: one move J3 `no-clear-sign→emerging` with `by: "run"`, J4 in `pendingOwner`, three evidence items `e1`-`e3`, a `nullCase` citing `e3`. Every case file is `{"rule": str, "ops": [...], "expect": str}`, with ops in the newsletter's format (`file` plus `set`/`del`/`append` key paths and `value`, or `write`, or `remove`).

- [ ] **Step 3: Write the failing tests** in `test_check_plugin.py`:

```python
class Base(unittest.TestCase):
    def test_base_passes(self):
        self.assertEqual(run_case(None), [])            # copies base to a temp dir, git init + commit, check()

    def test_duplicate_key_refused(self):
        with self.assertRaises(ValueError):
            jobslib.loads_json('{"a": 1, "a": 2}')

    def test_steps(self):
        self.assertEqual(jobslib.steps("no-clear-sign", "supported"), 2)
        self.assertEqual(jobslib.steps("contradicted", "no-clear-sign"), 1)

class Cases(unittest.TestCase):
    def test_every_case_fails_with_its_message(self):
        for path in sorted(CASES.glob("*.json")):
            case = json.loads(path.read_text())
            with self.subTest(case=path.stem):
                problems = run_case(case)
                self.assertTrue(any(case["expect"] in p for p in problems), problems)
```

One case file per rule, each `expect` the exact phrase below:

| case | breaks | expect |
|---|---|---|
| `claim_ids_order` | swap J1 and J2 in `claims` | `claims must be J0 to J12 in order` |
| `status_off_scale` | J0 `status: "likely"` | `status must be one of contradicted, no-clear-sign, emerging, supported, established` |
| `indicator_no_confounders` | J1 first indicator `confounders: []` | `indicator needs at least one confounder` |
| `indicator_datakind` | `dataKind: "public"` | `dataKind must be official or private` |
| `series_prefix` | `series: ["yahoo:ACN"]` | `series id must start with fred:, bls:, stooq: or basket:` |
| `history_chain` | J3 second row `from: "supported"` | `history row 2: from must equal the previous row's to` |
| `history_last` | J3 `status: "supported"` | `last history row's to must equal status` |
| `lens_mismatch` | J0 `lens: "work"` | `lens must be null for J0` |
| `marks_missing` | delete J5 `marks.supported` | `marks need contradicted, emerging, supported and established` |
| `pending_not_extreme` | J4 `pending.to: "emerging"` | `pending.to must be established or contradicted` |
| `strip_order` | edition 10-15 strip without J12 | `strip must list J0 to J12 in order` |
| `rating_off_set` | e1 `rating: "fact"` | `rating must be one of the six ratings` |
| `qual_long` | e1 `ratingQual: "part of this is our own inference"` | `ratingQual is at most 5 words` |
| `url_denylisted` | e1 `url: "https://aiweekly.co/x"` | `url is on the denylist (aiweekly.co)` |
| `url_scheme` | e1 `url: "ftp://x"` | `url must be http(s)` |
| `move_two_steps` | J3 move `from: "contradicted"` | `move of 2 steps needs by: owner` |
| `move_to_extreme` | J3 move `to: "established", from: "supported"` | `move to established needs by: owner` |
| `baseline_extreme` | 10-08 strip J4 `status: "established"` | `baseline may not start a claim at established` |
| `null_case_missing` | delete `nullCase` | `nullCase is required` |
| `headline_long` | 91-character headline | `headline is over 90 characters` |
| `dek_long` | 61-word dek | `dek is over 60 words` |
| `evidence_dangling` | J3 move `evidence: ["e9"]` | `evidence id e9 is not defined` |
| `evidence_id_twice` | e2 `id: "e1"` | `evidence id e1 is used twice` |
| `bears_direction` | e1 `bears[0].direction: "pro"` | `bears direction must be for or against` |
| `date_filename` | 10-15 `date: "2026-10-14"` | `date must match the file name` |

- [ ] **Step 4: Run to verify they fail.** Run: `python3 -m unittest discover -s scripts/tests -t .` Expected: errors importing `jobslib` / `check_plugin`.

- [ ] **Step 5: Implement `jobslib.py` and `check_plugin.py`** (claims and edition rules only; git rules are Task 2). `check()` loads `claims.json` and every `editions/*.json` with `load_json` (a load error is a problem, not a crash), runs `check_claims` and `check_edition`, and returns the problems sorted by file. `url_problem` lowercases the host and matches a denylisted domain or any subdomain of it.

- [ ] **Step 6: Run to verify they pass.** Run: `python3 -m unittest discover -s scripts/tests -t .` Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git add .gitignore LICENSE LICENSE-content.md README.md scripts/jobslib.py scripts/check_plugin.py scripts/tests
git commit -m "Scaffold the plugin and its data-contract checks"
```

### Task 2: Frozen-data rules against git

**Files:**
- Modify: `scripts/check_plugin.py` (add `check_git`)
- Modify: `scripts/tests/test_check_plugin.py`; create cases with `head_ops`

**Interfaces:**
- Consumes: `jobslib.git_show`, `jobslib.git_ok`, `check()` from Task 1.
- Produces: `check_git(root: Path, rev: str, claims: dict) -> list[str]`, called by `check()`. When `git_ok` is false it returns `[]` and `check()` prints `note: no git at <rev>; frozen checks skipped` (CLI only).

- [ ] **Step 1: Extend the harness.** A case may carry `head_ops`, applied to the base before the commit (default: the base as is), and `ops`, applied to the working tree after the commit.

- [ ] **Step 2: Write the failing cases:**

| case | breaks | expect |
|---|---|---|
| `edition_edited` | ops: change 10-08 `headline` | `editions/2026-10-08.json changed since HEAD; committed editions are frozen` |
| `edition_removed` | ops: remove 10-08 | `editions/2026-10-08.json was removed; committed editions are frozen` |
| `history_edited` | ops: J3 history row 1 `why: "x"` | `J3: history row 1 changed since HEAD; history is append-only` |
| `history_dropped` | ops: delete J3 history row 2 | `J3: history row 2 was removed; history is append-only` |
| `wording_changed_no_bump` | ops: J1 `wording: "x"` | `J1: wording changed since HEAD without a version bump and changelog entry` |
| `lists_changed_no_bump` | ops: `lists.laborPricedBasket` added | `lists changed since HEAD without a version bump and changelog entry` |

Also a passing test: `test_version_bump_allows_wording_change` (ops: J1 wording changed, `version: "1.1"`, a `changelog` entry appended) returns no problems; and `test_new_edition_is_not_frozen` (ops: write a valid `editions/2026-10-22.json`) returns no problems.

- [ ] **Step 3: Run to verify they fail.** Expected: the six cases FAIL with missing expected messages.

- [ ] **Step 4: Implement `check_git`.** Compare every committed `editions/*.json` (`git ls-tree --name-only <rev> editions/`) byte for byte with the working tree. For `claims.json` at `<rev>`: each claim's `history` at HEAD must be a prefix of the current one, row by row; `label`, `wording`, `marks`, `indicators` per claim and top-level `lists` and `defaultMarks` must be equal unless `version` differs and `changelog` gained an entry.

- [ ] **Step 5: Run to verify they pass.** Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add scripts/check_plugin.py scripts/tests
git commit -m "Frozen-data checks: editions, history, claim wording"
```

### Task 3: `confirm.py`

**Files:**
- Create: `scripts/confirm.py`, `scripts/tests/test_confirm.py`

**Interfaces:**
- Consumes: `jobslib.load_json`, `dump_json`, `STATUS`, `EXTREMES`.
- Produces: `apply(doc: dict, claim: str, to: str | None, reject: bool, today: str) -> tuple[dict, str]` (pure: the new claims document and the commit message); `main(argv) -> int` (writes `claims.json`, then `git add claims.json` and `git commit -m <message>`; exit 0, or 2 with the reason on stderr).

- [ ] **Step 1: Write the failing tests:**

```python
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
    self.assertEqual((j4["history"][-1]["from"], j4["history"][-1]["to"], j4["history"][-1]["note"]),
                     ("supported", "supported", "rejected: established"))
    self.assertEqual(msg, "Owner rejects J4: established")

def test_refuses_without_pending(self):
    with self.assertRaisesRegex(ValueError, "J3 has no pending move"):
        confirm.apply(claims(), "J3", "established", False, "2026-10-20")

def test_refuses_wrong_target(self):
    with self.assertRaisesRegex(ValueError, "J4's pending move is to established, not contradicted"):
        confirm.apply(claims(), "J4", "contradicted", False, "2026-10-20")

def test_result_passes_check_plugin(self):   # temp repo from the Task 1 base; main() commits; check() returns []
```

- [ ] **Step 2: Run to verify they fail.** Run: `python3 -m unittest scripts.tests.test_confirm` Expected: import error.
- [ ] **Step 3: Implement.** CLI: `confirm.py J4 --to established` or `confirm.py J4 --reject`; `--root` (default the repo root); `today` is the Pacific date (`TZ=America/Los_Angeles`).
- [ ] **Step 4: Run to verify they pass.** Expected: `OK`.
- [ ] **Step 5: Commit**

```bash
git add scripts/confirm.py scripts/tests/test_confirm.py
git commit -m "confirm.py: the owner's decision on a pending extreme"
```

### Task 4: `fetch_series.py`

**Files:**
- Create: `scripts/fetch_series.py`, `scripts/tests/test_fetch_series.py`, `scripts/tests/fixtures/http/` (saved responses: `fred_DFII10.csv`, `bls_ok.json`, `bls_refused.json`, `stooq_acn.csv`, `stooq_rsp.csv`, `captcha.html`)

**Interfaces:**
- Consumes: `jobslib.load_json`, `dump_json`, `SERIES_PREFIXES`.
- Produces: `series_ids(claims: dict) -> list[str]` (every indicator's `series`, sorted, unique); `fetch_one(sid: str, get) -> list[list]` (`[["YYYY-MM-DD" | "YYYY-MM" | "YYYY-Qn", float], …]`, from `START = "2015-01-01"`; raises `FetchError` on any bad body); `derive_basket(members: list[list[list]], comparison: list[list]) -> list[list]`; `run(root: Path, get=http_get, now: str | None = None) -> dict` (writes `series/<prefix>__<id>.json` and `series/releases.json`; returns `{"ok": [...], "stale": [...]}`); `main(argv) -> int` (exit 0, even with stale series; exit 2 on a malformed series id).
- Series file: `{"id", "url", "fetched", "status": "ok"|"stale", "error": str|null, "observations": [[date, value], …]}`. `releases.json`: `{"generated", "series": [{"id", "status", "new": [[date, value], …], "revised": [[date, old, new], …], "latest": [date, value] | null}]}`, where new and revised are against the file on disk before this run.
- Endpoints: FRED `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<ID>` (CSV; `.` is a missing value, skipped); BLS `https://api.bls.gov/publicAPI/v1/timeseries/data/<ID>` (JSON; `status` must be `REQUEST_SUCCEEDED`; period `M01`-`M12` → `YYYY-MM`, `Q01`-`Q04` → `YYYY-Qn`, `M13` skipped); Stooq `https://stooq.com/q/d/l/?s=<sym>&i=d` (CSV `Date,Open,High,Low,Close,Volume`; Close used). `basket:<list>` derives from `claims.lists[<list>].members[*].price` and `.comparison` (Stooq symbols): on dates every member and the comparison share, each member's close is indexed to 100 at the first shared date, members are averaged, and the result is divided by the comparison's index and multiplied by 100.
- `http_get(url) -> str`: urllib, 30 s timeout, User-Agent `post_agi_work fetch_series (contact: <SEC_CONTACT_EMAIL or git config user.email>)`; the contact is never written to disk.

- [ ] **Step 1: Write the failing tests:**

```python
def test_fred_parses_and_skips_missing(self):      # "." rows dropped; values floats; dates from START on
def test_bls_periods(self):                        # M02 -> "2026-02", Q03 -> "2026-Q3", M13 skipped
def test_bls_refusal_is_stale(self):               # bls_refused.json -> FetchError; run() keeps the old file, status "stale"
def test_html_body_keeps_last_good(self):          # captcha.html for a FRED id -> FetchError; old observations kept
def test_basket_index(self):                        # two members, one comparison, hand-computed expected values
def test_releases_new_and_revised(self):            # old file has 2026-08 = 1.0; new has 2026-08 = 1.1 and 2026-09 = 1.2
    self.assertEqual(rel["new"], [["2026-09", 1.2]])
    self.assertEqual(rel["revised"], [["2026-08", 1.0, 1.1]])
def test_malformed_id_exits_2(self):                # series "fred" (no colon) -> main() returns 2
```

- [ ] **Step 2: Run to verify they fail.** Run: `python3 -m unittest scripts.tests.test_fetch_series` Expected: import error.
- [ ] **Step 3: Implement.** A body that doesn't parse as the expected CSV header or JSON shape raises `FetchError`; `run()` catches per series, so one failure never stops the others. A basket whose member or comparison is stale is itself stale.
- [ ] **Step 4: Run to verify they pass.** Expected: `OK`.
- [ ] **Step 5: Check Stooq live.** Run: `curl -s -A "post_agi_work test" "https://stooq.com/q/d/l/?s=acn.us&i=d" | head -3`. Expected: a `Date,Open,High,Low,Close,Volume` header and rows. If it returns HTML, a captcha or an API-key notice, record "Stooq unavailable" for Task 5 (the J1 basket indicator is dropped from v1, as the spec allows) and keep the `stooq:` code (tested, unused).
- [ ] **Step 6: Commit**

```bash
git add scripts/fetch_series.py scripts/tests/test_fetch_series.py scripts/tests/fixtures/http
git commit -m "fetch_series.py: official and market series, basket, releases"
```

### Task 5: `claims.json` v1.0 and the first series pull

**Files:**
- Create: `claims.json`, `series/*.json` (via the script)

**Interfaces:**
- Consumes: the schema checked by Tasks 1-2; `fetch_series.run`.
- Produces: the v1.0 tracker every later task reads.

- [ ] **Step 1: Confirm sources, in parallel by lens.** For each lens, one research agent opens every candidate source the spec names in section 5.5 for its claims, and returns for each indicator: the confirmed name, publisher, URL (a page that was opened), cadence, `dataKind`, confounders, comparison, and series ids that exist (checked on FRED's or BLS's own series page). A source that can't be confirmed is dropped, never replaced by a guess. The same agents confirm the pinned lists in spec 5.3 against the companies' investor pages (Stooq symbols for the J1 basket; comparison `rsp.us`, the S&P 500 equal-weight ETF, as the index proxy, named as a proxy in the indicator).
- [ ] **Step 2: Write `claims.json`.** `version: "1.0"`, `changelog` one entry dated 2026-10-06, `scale` and `defaultMarks` from spec 5.1, `lists` from spec 5.3, the thirteen claims with `wording`, `why`, `marks` from spec 5.5 verbatim, the confirmed indicators, `status: "no-clear-sign"`, `since: null`, `pending: null`, `history: []` (the baseline writes the first rows). Revenue per employee and market concentration are read by agents from filings in v1 (`series: null`); the J1 basket is `series: ["basket:laborPricedBasket"]` only if Stooq passed Task 4 Step 5.
- [ ] **Step 3: Allow an empty history before the baseline.** Add the rule `history may be empty only when since is null and no edition exists` to `check_claims` with case `history_empty_after_baseline`, and make the Task 1 rule "last history row's to must equal status" skip claims with an empty history.
- [ ] **Step 4: Validate.** Run: `python3 scripts/check_plugin.py` Expected: `CHECK OK`. Run: `python3 -m unittest discover -s scripts/tests -t .` Expected: `OK`.
- [ ] **Step 5: First pull.** Run: `python3 scripts/fetch_series.py` Expected: exit 0 and one `series/*.json` per id; any `stale` series is investigated (a wrong id is fixed in `claims.json` before the commit, since v1.0 isn't committed yet).
- [ ] **Step 6: Commit**

```bash
git add claims.json series scripts/check_plugin.py scripts/tests
git commit -m "claims.json v1.0: J0-J12 with marks, indicators and pinned lists; first series pull"
```

### Task 6: The `jobs-weekly` workflow

**Files:**
- Create: `.claude/workflows/jobs-weekly.js`

**Interfaces:**
- Consumes: `claims.json`, `series/releases.json`, the newest `editions/*.json`, `scripts/check_plugin.py`.
- Produces: writes `editions/<date>.json` and `claims.json` (`status`, `since`, `pending`, appended `history` only); returns `{ready: bool, headline, moves, pendingOwner, gaps, fallbacks, review}`.

- [ ] **Step 1: Load the `workflow-authoring` skill** and read the newsletter's `.claude/workflows/weekly-wrapup.js` for the house patterns: args parsing (object or JSON text), `agentMax()`, `GROUND`/`EVIDENCE` prompt blocks, schemas as JSON Schema objects, `pipeline()` for research-then-verify per lens, `phase()` names matching `meta.phases`.
- [ ] **Step 2: Write the script.** `meta.phases`: Research, Verify, Decide, Write, Review. Args: `date` (required, `YYYY-MM-DD`), `baseline` (default false), `repo` (default `/Users/joeldg/Projects/post_agi_work`), `only` (optional list of lens keys, for a rehearsal), `researchBy`, `writeBy`. Scratch: `<repo>/.claude/work/jobs-<date>/`. Prompt blocks:
  - `GROUND`: the repo, the hard limits (no git commands that change anything; write only the files the stage names; scratch only under the work folder; load `WebSearch,WebFetch` with ToolSearch; open every source; never invent a URL, date, number or quote; the Pacific clock and the soft deadlines).
  - `EVIDENCE`: spec section 6 in full, plus: official series and prices come only from `series/` (quote a value with its series id and observation date); name the confounder; "consistent with" readings are "our inference".
  - `MARKS`: spec 5.1 and 5.2 in full, and "the marks in claims.json are the rule; quote the mark you apply".
  - Research prompt per lens: its claims' full `claims.json` entries, the window (`baseline`: the evidence base to date, items before the window marked `background`; otherwise from the day after the previous edition's date to `date`), `series/releases.json`, the previous edition. The `null` lens prompt: find only the strongest evidence that this is a normal technology transition, across every claim's area.
  - Verifier (per lens, as each lands): assume every item is wrong until its source proves it; verdict, final rating, `via`. Items with `material: true` also go to a second independent refuter.
  - Decide: apply each claim's marks to the verified items, the series and the history; propose moves (one step; extremes to `pendingOwner`; baseline: starting statuses per spec 5.2 rule 6); then a move refuter; drop moves it breaks.
  - Write: the edition (schema of spec 4.2) and the allowed `claims.json` updates; run `python3 scripts/check_plugin.py` until `CHECK OK`.
  - Review: hostile reviewer (sourcing, ratings, attribution, dates, named confounders, null case, overclaiming, investment language, only allowed `claims.json` fields changed), then a fixer that reruns `check_plugin.py`.
- [ ] **Step 3: Rehearse the plumbing.** Copy the repo to a scratch directory (`cp -R`, including `.git`), then run `Workflow({scriptPath: "<repo>/.claude/workflows/jobs-weekly.js", args: {date: "<today>", baseline: true, repo: "<scratch>", only: ["null"]}})`. Expected: the run ends with `ready: true`, and `python3 scripts/check_plugin.py` in the scratch copy prints `CHECK OK` (the strip lists all thirteen claims; claims outside the lens keep `no-clear-sign` with a reason saying no lens ran). Fix and rerun until it does. Note the usage before and after (the `get_usage` tool).
- [ ] **Step 4: Commit**

```bash
git add .claude/workflows/jobs-weekly.js
git commit -m "The jobs-weekly workflow"
```

### Task 7: README and the routine text

**Files:**
- Modify: `README.md`
- Create: `docs/routine.md`

- [ ] **Step 1: Write `docs/routine.md`.** Spec section 7.1 as instructions to a fresh session: preflight (Thursday date, duplicate, `git pull --ff-only`, clean tree for `claims.json editions series scripts`, the usage valve at 70% of the 5-hour window or 75% of any weekly window via `mcp__ccd_session_mgmt__get_usage`), `fetch_series.py`, the workflow by `scriptPath` with `{date}`, `check_plugin.py`, the explicit-path commit and push, the push notification (headline, moves, `pendingOwner` with its `confirm.py` command, earlier unconfirmed items, gaps), the 06:00 Friday restore rule, the manual-rerun rule, and the final output.
- [ ] **Step 2: Write `README.md`.** What the plugin is (one paragraph), the status scale, the files, the contract with the newsletter (`import_jobs.py` reads committed `HEAD` only; exit codes 0/2/3), how to run the tests, `fetch_series.py`, `check_plugin.py`, `confirm.py`, how to rehearse, and the licenses.
- [ ] **Step 3: Verify.** Run: `python3 scripts/check_plugin.py && python3 -m unittest discover -s scripts/tests -t .` Expected: `CHECK OK` and `OK`.
- [ ] **Step 4: Commit and push**

```bash
git add README.md docs/routine.md
git commit -m "README and the routine instructions"
git push -u origin main
```

### Task 8: The baseline

**Files:**
- Create: `editions/<today>.json`; modify: `claims.json` (status, since, pending, history), `series/`

- [ ] **Step 1: Usage valve.** Call `get_usage`. If the 5-hour window is at 70% or more, or any weekly window at 75% or more, stop and tell the owner (tomorrow's 09:02 daily comes first).
- [ ] **Step 2: Refresh series.** Run: `python3 scripts/fetch_series.py` Expected: exit 0.
- [ ] **Step 3: Run the workflow.** `Workflow({scriptPath: "/Users/joeldg/Projects/post_agi_work/.claude/workflows/jobs-weekly.js", args: {date: "<today>", baseline: true}})`. Expected: `ready: true`.
- [ ] **Step 4: Validate.** Run: `python3 scripts/check_plugin.py && python3 -m unittest discover -s scripts/tests -t .` Expected: `CHECK OK`, `OK`. Read the edition: thirteen strip entries, no claim at an extreme, every move-free baseline row with a reason, a null case.
- [ ] **Step 5: Commit and push**

```bash
git add editions/<today>.json claims.json series
git commit -m "Baseline edition <today>"
git push origin main
```

- [ ] **Step 6: Report** the headline, each claim's starting status, the `pendingOwner` items with their `confirm.py` commands, the gaps, and the usage the run took.

### Task 9: The Thursday routine (owner approval required)

- [ ] **Step 1: Ask the owner** to approve creating the scheduled task: id `jobs-weekly`, cron `7 19 * * 4` (local time, Pacific), first effective run the first Thursday at least five days after the baseline.
- [ ] **Step 2: On a yes,** create it with `mcp__scheduled-tasks__create_scheduled_task`: prompt "Follow /Users/joeldg/Projects/post_agi_work/docs/routine.md exactly. Work in /Users/joeldg/Projects/post_agi_work." plus the owner's goal line. Run: `mcp__scheduled-tasks__list_scheduled_tasks`. Expected: `jobs-weekly` enabled with the next run on the right Thursday at 19:07.
