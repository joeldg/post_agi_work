# Jobs plugin for Hidden AGI watch

A weekly **thesis tracker** on the transition to a post-AGI economy: what is already happening to work and capital, and how businesses and investors are positioning ahead of AI, AGI, recursive self-improvement and ASI. Its core lens is that capital is forward-looking: firms and markets act on what they expect AI to do before it shows in employment data, so their positioning is the earliest evidence.

It is published as the **"Jobs"** section of the [Hidden AGI watch](https://hiddenagi.com/) Friday wrap-up and on a standing page, `jobs.html`. It never feeds the newsletter's Hidden AGI Index, odds, gauges, signals or fire alarm. It is not investment advice.

The design is in [`docs/superpowers/specs/2026-10-06-jobs-plugin-design.md`](docs/superpowers/specs/2026-10-06-jobs-plugin-design.md).

## The claims

Thirteen testable claims, `J0` to `J12`, in [`claims.json`](claims.json): each with its wording, the written **marks** that decide its status, its indicators (source, cadence, official or private data, confounders, comparison group) and an append-only history. `J0` is the null hypothesis, "so far, a normal technology transition", and every edition reports the strongest evidence for it.

| Status | Means |
|---|---|
| Contradicted | The main indicators move against the claim in two independent sources, across two releases |
| No clear sign | Flat, mixed, within the pre-2022 range, or explained by a named confounder (the default) |
| Emerging | One primary indicator moves the claim's way beyond its pre-2022 range or comparison group |
| Supported | Two independent indicators of different kinds agree, across two releases |
| Established | Supported for two quarters, in official statistics, with no live alternative explanation |

A claim moves at most one step a week. A move to Established or Contradicted is only ever proposed; the owner confirms or rejects it. The claims' wording, marks, indicators and pinned lists change only with a version bump and a changelog entry.

## Files

| Path | What it holds |
|---|---|
| `claims.json` | The tracker: the claims, marks, indicators, pinned lists, current statuses and history |
| `editions/YYYY-MM-DD.json` | One edition per run (Thursdays; the first is the baseline). Frozen once committed |
| `series/` | Official series pulled by `fetch_series.py`, one file per series, and `releases.json` (what is new) |
| `scripts/fetch_series.py` | Pulls the series named in `claims.json` from FRED and the BLS public API, keyless; a failed series keeps its last good data and reads as stale |
| `scripts/state.py` | Prints what a run starts from: statuses, the previous edition, the owner's confirmations, new releases |
| `scripts/apply_edition.py` | The workflow's write step: writes an edition and the allowed `claims.json` fields, then validates |
| `scripts/check_plugin.py` | The validator: the data contract and the frozen-data rules against git |
| `scripts/confirm.py` | The owner's decision on a pending move: `python3 scripts/confirm.py J4 --to established` or `--reject` (commits locally) |
| `.claude/workflows/jobs-weekly.js` | The weekly workflow: research, adversarial verification, decision, write, review |
| `docs/routine.md` | The scheduled task's instructions (Thursdays, about 19:07 Pacific) |

## The contract with the newsletter

The newsletter's wrap-up runs `scripts/import_jobs.py --date <FRIDAY>` (in `agi_assessment`). It reads this repo's **committed `HEAD` only**, takes the newest edition dated in the seven days up to the Friday, validates it with its own checker, and copies it and `claims.json` into its `data/jobs/`. Exit 0: imported; 3: no plugin or no edition (the wrap-up goes out without Jobs); 2: invalid, refused. This repo never writes into the newsletter repo.

## Running

```sh
python3 -m unittest discover -s scripts/tests -t .   # tests: stdlib, no network
python3 scripts/fetch_series.py                      # refresh series/
python3 scripts/check_plugin.py                      # CHECK OK or the problems
```

A rehearsal runs the workflow on a scratch copy of the repo (`cp -R`), with `Workflow({scriptPath: ".../jobs-weekly.js", args: {date, baseline: true, repo: "<scratch copy>", only: ["null"]}})`; nothing in the real repo changes.

Python 3.9 or newer, standard library only.

## License

Code: MIT ([`LICENSE`](LICENSE)). The claims, editions and docs: CC BY 4.0 ([`LICENSE-content.md`](LICENSE-content.md)); third-party material and the series data stay under their owners' terms.
