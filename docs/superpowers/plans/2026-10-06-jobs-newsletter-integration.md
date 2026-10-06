# Jobs plugin: newsletter integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Hidden AGI watch wrap-up import the newest Jobs edition when one exists, render it as the last section ("Jobs") of the page and email, publish `jobs.html`, and check it all.

**Architecture:** A new `scripts/import_jobs.py` copies the plugin's committed edition and claims into `data/jobs/`; `build_weekly.py` renders a Jobs section only when `data/jobs/<DATE>.json` exists; a new page module renders `jobs.html`; a new `checks/jobs.py` enforces the contract and frozen data. With no plugin or edition, every output is byte-identical to today's.

**Tech Stack:** Python 3.9+ standard library, the newsletter's existing scripts and `unittest` harness.

**Spec:** `docs/superpowers/specs/2026-10-06-jobs-plugin-design.md` (in `joeldg/post_agi_work`), sections 8-10.

**Where:** the newsletter repo `joeldg/agi_assessment`, on `redesign-v2` or a branch off it, in a worktree. **When:** after the redesign is live; Task 6 only after the owner approves. Prerequisite: the plugin plan (`2026-10-06-jobs-plugin.md`) is done, so a real edition exists to rehearse with.

## Global Constraints

- Everything in the plugin plan's Global Constraints that applies to data: claim ids, status ids and labels, ratings, kinds, limits, denylist (here the newsletter's own `DENYLIST` in `scripts/check_data.py` is authoritative).
- No change to any output when `data/jobs/<DATE>.json` is absent: past wrap-ups, pages and emails rebuild byte for byte.
- The Jobs section never feeds the Index, odds, gauges, signals or alarm, and never appears in an email subject.
- Email Jobs block ≤ 200 words (a `check_data.py --pages` warning, not an error).
- `jobs.html` is a child of the "Today" hub (`index.html`), crumb title "Jobs watch"; anchors `#J0` … `#J12`.
- Display words for statuses: Contradicted, No clear sign, Emerging, Supported, Established.
- Follow the newsletter's own rules: pages via `sitekit.page()`, escapes via `html.escape`, JSON style `indent=1, ensure_ascii=False` plus a trailing newline, commits of explicit paths only.

## Review Focus

1. The plugin checkout has an uncommitted, half-written edition: the import must read `HEAD` only and ignore it (Task 2, `test_reads_head_only`).
2. Two editions in the window (a Thursday and a manual Friday rerun): the newest wins (Task 2, `test_newest_in_window`).
3. The import runs twice for the same Friday: corrections are appended once, files identical (Task 2, `test_rerun_is_idempotent`).
4. An edition's evidence text holds `<script>` or `&`: it must be escaped on the page and in the email (Task 3, `test_text_is_escaped`).
5. A pending extreme on the strip: shown as "under review", never as the new status (Task 3, `test_pending_shows_under_review`).

---

### Task 1: `checks/jobs.py`

**Files:**
- Create: `scripts/checks/jobs.py`, fixtures under `scripts/tests/fixtures/checks/base/data/jobs/` (a valid `2026-10-09.json` and `claims.json`, copied from the plugin's test fixtures and renamed to a Friday) and cases `jobs_*.json` under `scripts/tests/fixtures/checks/cases/`
- Modify: `scripts/check_data.py` (parse `data/jobs/*.json` with the others at the glob near line 142; call `ck_jobs.check(ctx)` next to `ck_components.check` near line 942), `scripts/checks/__init__.py` (docstring list), `scripts/tests/test_checks.py` (the default `call` set includes `jobs`)

**Interfaces:**
- Produces: `check(ctx) -> None` (reports through `ctx.f`), `validate_edition(doc: dict) -> list[str]`, `validate_claims(doc: dict) -> list[str]` (pure; reused by `import_jobs.py`).

- [ ] **Step 1: Write the failing cases**, one per rule, in the existing case format (`ops`, `head_ops`, `expect`): `jobs_rating_off_set` (`rating must be one of the six ratings`), `jobs_url_denylisted` (`is on the denylist`), `jobs_status_off_scale` (`status must be one of`), `jobs_move_two_steps` (`move of 2 steps needs by: owner`), `jobs_history_edited` (`history is append-only`), `jobs_edition_edited` (`data/jobs/2026-10-09.json changed since HEAD; published Jobs editions are frozen`), `jobs_wording_no_bump` (`without a version bump and changelog entry`), `jobs_strip_order` (`strip must list J0 to J12 in order`).
- [ ] **Step 2: Run to verify they fail.** Run: `python3 -m unittest discover -s scripts/tests -p 'test_checks.py'` Expected: the eight `jobs_*` cases FAIL; all others still pass.
- [ ] **Step 3: Implement.** Port the plugin's `check_claims`/`check_edition` rules into the pure validators, using `ctx.check_url` for URLs; frozen rules use `ctx.git` like the other modules. Every rule is a no-op while `data/jobs/` doesn't exist.
- [ ] **Step 4: Run to verify they pass.** Expected: `OK`. Run: `python3 scripts/check_data.py` on the real tree. Expected: passes (no `data/jobs/` yet).
- [ ] **Step 5: Commit** `scripts/checks/jobs.py scripts/checks/__init__.py scripts/check_data.py scripts/tests` ("checks/jobs.py: the Jobs data contract").

### Task 2: `scripts/import_jobs.py`

**Files:**
- Create: `scripts/import_jobs.py`, `scripts/tests/test_import_jobs.py`

**Interfaces:**
- Consumes: `checks.jobs.validate_edition`, `validate_claims`.
- Produces: `find_plugin(arg: str | None, root: Path) -> Path | None` (`--plugin`, then `$JOBS_PLUGIN`, then `root.parent / "post_agi_work"`; a directory whose `HEAD` has `claims.json`); `pick_edition(plugin: Path, friday: str) -> tuple[str, str] | None` (the newest `editions/YYYY-MM-DD.json` at `HEAD` dated from `friday - 6 days` to `friday`, as `(date, text)`); `import_edition(root: Path, plugin: Path | None, friday: str) -> tuple[int, str]` (exit code and one line); `main(argv) -> int`.
- Writes: `data/jobs/<friday>.json` (the edition plus `"edition": <date>` and `"source": "post_agi_work@<short sha>"`), `data/jobs/claims.json`, and appends each edition correction to `data/corrections.json` `corrections` with `"emailed": null, "section": "jobs"` unless an entry with the same `date`, `item` and `section` exists.
- Exit codes: 0 imported; 3 no plugin or no edition in the window; 2 invalid (nothing written).

- [ ] **Step 1: Write the failing tests** (each builds a temp plugin git repo and a temp newsletter root): `test_no_plugin_exits_3`, `test_no_edition_in_window_exits_3`, `test_imports_newest_in_window` / `test_newest_in_window` (editions 10-02, 10-08 and 10-09 for Friday 10-09 → 10-09), `test_reads_head_only` (an uncommitted `editions/2026-10-09.json` is ignored; the committed 10-08 is imported), `test_invalid_edition_exits_2_and_writes_nothing`, `test_corrections_appended_once`, `test_rerun_is_idempotent` (byte-identical files after two runs).
- [ ] **Step 2: Run to verify they fail.** Run: `python3 -m unittest scripts.tests.test_import_jobs` Expected: import error.
- [ ] **Step 3: Implement.** Read files with `git -C <plugin> show HEAD:<path>` and list with `git -C <plugin> ls-tree --name-only HEAD editions/`.
- [ ] **Step 4: Run to verify they pass.** Expected: `OK`.
- [ ] **Step 5: Commit** `scripts/import_jobs.py scripts/tests/test_import_jobs.py` ("import_jobs.py: bring in the week's Jobs edition").

### Task 3: The Jobs section in the wrap-up

**Files:**
- Modify: `scripts/build_weekly.py` (load in `build()`, render in `page_body()` and `weekly_email_html_v2()`)
- Create: `scripts/jobs_render.py` (shared by the wrap-up and `jobs.html`), `scripts/tests/test_jobs_render.py`

**Interfaces:**
- Produces (`jobs_render.py`): `STATUS_LABEL: dict`, `strip_html(ed: dict) -> str` (each claim: id, label, status word, an up or down arrow when `prev` differs, "under review" when `pending`), `section_html(ed: dict, claims: dict, root: str = "../") -> str` (the page section, `<section id="jobs"><h2>Jobs</h2>…`), `email_lines(ed: dict, site: str) -> list[str]` (email-safe HTML blocks using `build_feed`'s `h2`, `p`, `ul`, `link`).
- `build()` sets `w["jobs"]` from `data/jobs/<date>.json` when it exists (and `w["jobsClaims"]` from `data/jobs/claims.json`); otherwise neither key is set.

- [ ] **Step 1: Write the failing tests:** `test_absent_changes_nothing` (`page_body(w)` and `weekly_email_html_v2(w)` for a `w` without `jobs` equal the output computed before this change, captured as fixtures from the current code first), `test_section_is_last` (the Jobs `<section id="jobs">` comes after the last standard section and before the frozen-data note), `test_baseline_says_starting_statuses`, `test_no_moves_line` ("No claim moved this week" plus at most three top evidence items), `test_pending_shows_under_review`, `test_text_is_escaped` (`<script>` in evidence text appears as `&lt;script&gt;`), `test_email_block_under_200_words` for the fixture edition, `test_subject_unchanged`.
- [ ] **Step 2: Run to verify they fail.** Expected: import error / failures.
- [ ] **Step 3: Implement.** Page section contents per spec 8.2: headline, dek, strip, moves with reasons, top evidence with `build_report.chip()` rating chips and source links, the null case, the week's releases, `Full tracker →` to `../jobs.html`. Email: after the section notes, before the closing links: `h2("Jobs")`, the headline, one sentence per move, one line for the null case, `Full tracker →`.
- [ ] **Step 4: Run to verify they pass.** Run: `python3 -m unittest discover -s scripts/tests -t .` Expected: `OK`.
- [ ] **Step 5: Commit** `scripts/build_weekly.py scripts/jobs_render.py scripts/tests/test_jobs_render.py` ("The Jobs section in the wrap-up").

### Task 4: `jobs.html`

**Files:**
- Create: `scripts/pages/jobs.py`
- Modify: `scripts/build_pages.py` (register `PAGES["jobs.html"]`), `scripts/sitekit.py` (`NAV`: add `"jobs.html"` to the `index.html` children; `CRUMB_TITLES["jobs.html"] = "Jobs watch"`), the naming key on `start-here.html#names` (one line for the Jobs scale), `scripts/tests/test_build_pages.py`

**Interfaces:**
- Consumes: `jobs_render.strip_html`, `STATUS_LABEL`.
- Produces: `pages.jobs.body() -> str | None` (None when `data/jobs/claims.json` is absent; `build_pages.py` then skips the page).

- [ ] **Step 1: Write the failing tests:** `test_jobs_page_skipped_without_data`, `test_jobs_page_has_every_claim_anchor` (`id="J0"` … `id="J12"`), `test_jobs_crumb_is_today` (`sitekit.crumb_for("jobs.html")` contains `Today` and `Jobs watch`), `test_jobs_intro_says_it_never_feeds_the_index`, `test_archive_links_wrapups` (one entry per `data/jobs/<date>.json`, linking `weekly/<date>.html`).
- [ ] **Step 2: Run to verify they fail.**
- [ ] **Step 3: Implement** per spec 8.3: a one-line glance, the intro (what it is; never feeds the Index, the odds or the alarm; the thesis and its end state as framing; how to read the scale), the status board, each claim collapsed with `sitekit`'s `fold()` under its id (wording, marks, indicators with source, cadence, data kind, confounders, comparison, and history), the newest edition's evidence, the archive.
- [ ] **Step 4: Run to verify they pass.** Expected: `OK`.
- [ ] **Step 5: Commit** `scripts/pages/jobs.py scripts/build_pages.py scripts/sitekit.py scripts/tests/test_build_pages.py` plus the start-here source if it lives elsewhere ("jobs.html: the Jobs watch page").

### Task 5: Smoke, sitemap, budgets and the README

**Files:**
- Modify: `scripts/smoke.py` (`STANDING` gains `jobs.html`; its `#J0`-`#J12` anchors are promised), `scripts/build_feed.py` (`STANDING_PAGES` gains `jobs.html`), `scripts/checks/pages.py` (`BUDGETS` gains `jobs.html`; the weekly email's Jobs block budget 200 words), `README.md` (a "Jobs plugin" section; Layout rows for `data/jobs/`, `jobs.html`, `scripts/import_jobs.py`, `scripts/jobs_render.py`; the wrap-up procedure's import step)

- [ ] **Step 1: Rehearse end to end** in the worktree: `python3 scripts/import_jobs.py --date <a Friday within 6 days of the plugin's newest edition> --plugin /Users/joeldg/Projects/post_agi_work` (expect exit 0), then `python3 scripts/build_weekly.py <that Friday> --allow-stale`, `python3 scripts/build_pages.py`, `python3 scripts/build_feed.py`, `python3 scripts/check_data.py`, `python3 scripts/check_data.py --pages`, `python3 scripts/smoke.py --widths 375,1280 --anchors`. Expected: all pass; the Jobs section and `jobs.html` render at both widths. Then restore the worktree (`git checkout --` and `git clean` on the generated files): the rehearsal is never committed.
- [ ] **Step 2: Run the unit tests.** `python3 -m unittest discover -s scripts/tests -t .` Expected: `OK`.
- [ ] **Step 3: Commit** the four modified files ("Jobs: smoke, sitemap, budgets, README").

### Task 6: The wrap-up routine (owner approval; after go-live)

**Files:**
- Modify: `/Users/joeldg/.claude/scheduled-tasks/weekly-agi-wrapup/SKILL.md` (private; via `mcp__scheduled-tasks__update_scheduled_task`)

- [ ] **Step 1: Ask the owner** to approve the routine change.
- [ ] **Step 2: On a yes,** add a step after "Validate what the updates wrote" and before "Build and check": run `python3 scripts/import_jobs.py --date <DATE>` and record the exit code (0 imported, 3 skipped, 2 refused: carry on without Jobs, put the reason at the top of the final output and in a push notification). Step 5's `git add` list gains, when changed, `data/jobs/<DATE>.json data/jobs/claims.json jobs.html` (`data/corrections.json` is already listed). The final output gains one line: "Jobs: imported <edition date> / skipped (no edition) / refused (<reason>)".
- [ ] **Step 3: Verify** with `mcp__scheduled-tasks__list_scheduled_tasks` and by reading the updated SKILL.md.
