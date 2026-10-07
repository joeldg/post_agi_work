# The jobs-weekly routine

Instructions for the scheduled task `jobs-weekly` (Thursdays at about 19:07 Pacific). Each run starts fresh: follow these steps exactly, in `/Users/joeldg/Projects/post_agi_work`, and run every command from that directory. The design is `docs/superpowers/specs/2026-10-06-jobs-plugin-design.md` (section 7.1).

GOAL (the owner's, for the newsletter this feeds): a newsletter "valuable to a degree that I would pay for it", at $5-10 a month. Every source, number and sentence in the edition should earn that: specific, sourced, rated and worth the reader's minutes.

This routine never touches the newsletter repo (`agi_assessment`). The Friday wrap-up imports the edition from this repo's committed `HEAD`.

## 0. Preflight

- `TODAY=$(TZ=America/Los_Angeles date +%F)`, `NOW=$(TZ=America/Los_Angeles date +%H:%M)`, `DOW=$(TZ=America/Los_Angeles date +%u)` (4 is Thursday).
- **DATE.** On a scheduled run, DATE is TODAY and DOW must be 4. On any other day, report the missed run in one line ("Jobs: no edition this week, the Thursday run did not happen"), send a push notification saying so, and stop. A **manual rerun** is the owner's call: when the owner starts this routine by hand and names a Thursday DATE, it is accepted until 11:00 PT the next day and must finish by then. The baseline is never run by this routine.
- **Duplicate.** If `editions/<DATE>.json` exists, stop: say so in one line and commit nothing.
- **Clean start.** `git pull --ff-only` (stop and report if it refuses). `git status --porcelain`: if anything is uncommitted under `claims.json`, `editions/`, `series/`, `scripts/` or `.claude/workflows/`, stop before editing anything, send a push notification ("Jobs <DATE>: run STOPPED, uncommitted work in <paths>") and put the same line at the top of the final output. If `main` is ahead of `origin/main` (for example the owner ran `confirm.py`, which commits locally), that is expected: today's push publishes those commits too; name them in the final output.
- **Usage valve.** Load the usage tool with ToolSearch (`select:mcp__ccd_session_mgmt__get_usage`) and call it. If the 5-hour window is at 70% or more, or any weekly window (every window whose label starts with "Weekly") is at 75% or more, **skip this week**: send a push notification ("Jobs <DATE>: skipped, usage at <n>% (<window>); no edition this week") and stop. Jobs always comes second to the newsletter's own daily and wrap-up runs.

## 1. Series

`python3 scripts/fetch_series.py`. It exits 0 even when a series fails; note every `WARN stale:` line for the final output. Exit 2 (a malformed series id in `claims.json`) stops the run: restore (see below) and report.

## 2. The workflow

Run `Workflow({scriptPath: "/Users/joeldg/Projects/post_agi_work/.claude/workflows/jobs-weekly.js", args: {date: DATE}})`, with `args` as an object, never a JSON-encoded string. It researches, verifies, decides, writes `editions/<DATE>.json` and the allowed `claims.json` fields, and reviews; it never commits. Read its result: `ready`, `headline`, `moves`, `pendingOwner`, `gaps`, `fallbacks`, `review`, `check`.

If it throws, or returns `ready: false` and the problems are not few and clear enough to fix by hand under the spec's rules, restore and report.

## 3. Validate

- `python3 scripts/check_plugin.py` must print `CHECK OK`.
- `python3 -m unittest discover -s scripts/tests -t .` must pass.
- Read `editions/<DATE>.json`: thirteen strip entries, a null case, a headline of at most 90 characters, no move of more than one step, no applied move to Established or Contradicted.
- `git status --porcelain` lists only `editions/<DATE>.json`, `claims.json` and files under `series/`. Anything else this run changed is undone.

## 4. Commit and push

Explicit paths only; never `git add -A`, `git add .`, `-f` or `--force`.

```
git add editions/<DATE>.json claims.json series
git diff --cached --name-only        # must list only those paths
git commit -m "Jobs edition <DATE>"
git pull --ff-only && git push origin main
```

If the pull or push is refused, stop and report; never force-push.

## 5. Notify the owner

Load the tool with ToolSearch (`select:PushNotification`) if needed, and send one notification: "Jobs <DATE>: <headline>. Moves: <list or none>. For you: <each pendingOwner item as `python3 scripts/confirm.py J4 --to established` or `--reject`, or none>. Gaps: <count>."

## 6. Final output, then stop

At the top: any STOPPED, skipped, restored or failed state. Then the headline, every claim's status (the strip), the moves, the items awaiting the owner with their `confirm.py` commands (including any still pending from earlier weeks), stale series, gaps, the workflow's `fallbacks`, and the commit pushed. Do not keep working in the session after the final output.

## Restoring

Whenever this routine stops after step 1 without committing, and at the latest at **06:00 PT Friday** for anything still uncommitted: `git checkout -- claims.json series`, then `git clean -f -- editions/<DATE>.json series` (only files this run created), so the next run starts clean. Say "restored" at the top of the final output and in a push notification. There is then no edition this week, and the Friday wrap-up goes out without Jobs.
