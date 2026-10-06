# Jobs plugin for Hidden AGI watch: design

- **Date:** 2026-10-06
- **Status:** approved in conversation, section by section; this document is the written spec for the owner's review.
- **Repos:** the plugin is `joeldg/post_agi_work` (public, this repo, local checkout `/Users/joeldg/Projects/post_agi_work`). The newsletter is `joeldg/agi_assessment` (public, GitHub Pages at <https://hiddenagi.com/>); its side of this design goes on the `redesign-v2` branch (format 2), which is not yet merged into `main`.

## 1. Purpose

A weekly **thesis tracker** on the transition to a post-AGI economy: what is already happening to work and capital, and how businesses and investors are positioning ahead of AI, AGI, recursive self-improvement and ASI. The core lens is that **capital is forward-looking**: firms and markets act on what they expect AI to do before it shows in employment data, so their positioning is the earliest evidence.

It appears once a week as the **last section of the Friday wrap-up**, under its own header, **"Jobs"**, and on a standing page, **`jobs.html`** ("Jobs watch").

The thesis comes from the owner's conversation with another AI model about jobs after AGI. That conversation is a source of **hypotheses, not facts**: none of its citations are used, and every claim below is tracked, not endorsed. The tracker exists to show, on evidence, whether the thesis holds.

### 1.1 What it is not

- It never feeds the Hidden AGI Index, the A–D odds, AGI anywhere, the gauges, the signals or the fire alarm.
- It is not a daily section, not a separate email, and never in an email subject.
- It is not investment advice. It names companies and pinned baskets as evidence; it never says buy, sell or hold, and never gives price targets. The newsletter's standing disclaimer applies.
- It does not add forecasts to the scorecard (possible later; out of scope now).

### 1.2 Decisions made while designing (2026-10-06)

| Decision | Choice |
|---|---|
| Editorial stance | Thesis tracker: explicit testable claims, evidence for and against each, a null hypothesis |
| Cadence | Weekly, entirely separate from the daily research |
| Where it appears | The Friday weekly wrap-up, as its last section, header "Jobs"; plus `jobs.html` |
| Run time | Thursdays at about 19:07 Pacific |
| Status display | A published, two-way status scale with written marks per claim |
| Architecture | A separate plugin repo; the wrap-up imports the newest edition if one exists (approach 1 of 3) |
| Standing page hub | "Today" (see 8.3: "the money hub" was approved, but `money.html` is a child of "Could it be hidden?", which would misfile Jobs) |
| Extremes | Moves to Established or Contradicted wait for the owner's confirmation |
| Baseline | Once built, a full run is made and committed to set the baseline (owner, 2026-10-06) |

## 2. Architecture

```
Thursday ~19:07 PT                         Friday ~13:11 PT (weekly-agi-wrapup routine)
post_agi_work (this repo)                  agi_assessment (newsletter)
-----------------------------              -----------------------------------------
fetch_series.py -> series/                 import_jobs.py --date <FRIDAY>
jobs-weekly workflow                         reads post_agi_work at git HEAD only
  research -> verify -> decide             -> data/jobs/<FRIDAY>.json, data/jobs/claims.json
  -> write -> review                       -> data/corrections.json (jobs corrections)
check_plugin.py                            build_weekly.py  -> "Jobs" section (page + email)
commit + push                              build_pages.py   -> jobs.html
notify owner                               check_data.py / checks/jobs.py, smoke.py
```

The plugin never writes into the newsletter repo. The newsletter never runs the plugin. The only contract between them is the two JSON files described in section 4, read from the plugin's committed `HEAD`, so a half-finished Thursday run is invisible to the newsletter.

**"If it exists it's included, if not, nothing":** no plugin checkout, no edition in the week, or an invalid edition all leave the wrap-up exactly as it is today.

## 3. The plugin repo

```
post_agi_work/
  README.md                  what the plugin is, the contract with the newsletter, how to run it
  LICENSE                    MIT, for the code
  LICENSE-content.md         CC BY 4.0, for claims.json and the editions
  .gitignore                 .claude/work/, __pycache__/
  claims.json                the tracker: J0-J12, marks, indicators, pinned lists, status, history
  series/                    official and market series pulled by script, one JSON file per series
    releases.json            what fetch_series.py found new since the last edition
  editions/YYYY-MM-DD.json   one per run, named by the run's date (a Thursday, except the baseline); the only file the newsletter imports per week
  scripts/
    fetch_series.py          pulls pinned series from public endpoints; stdlib only; never hand-edited output
    check_plugin.py          validates claims.json and every edition; frozen-data checks against git
    confirm.py               the owner confirms or rejects a pending move
    tests/                   stdlib unittest, with fixtures
  .claude/workflows/jobs-weekly.js   the Thursday workflow (committed)
  .claude/work/              scratch for a run (git-ignored)
  docs/superpowers/specs/    this document
```

Python 3.9 or newer, standard library only, like the newsletter (the scheduled tasks use the system `python3`).

## 4. Data files

Stored status values are ids; display words are separate (the newsletter's "one word, one meaning" rule).

| id | Display word | Order |
|---|---|---|
| `contradicted` | Contradicted | 0 |
| `no-clear-sign` | No clear sign | 1 |
| `emerging` | Emerging | 2 |
| `supported` | Supported | 3 |
| `established` | Established | 4 |

These words are new to the site and collide with none in use (Level, rung, Quiet/Open/Confirmed, Far/Partial/Close/Met).

### 4.1 `claims.json`

```json
{
  "schema": 1,
  "version": "1.0",
  "changelog": [{"version": "1.0", "date": "2026-10-06", "note": "First version."}],
  "scale": [{"id": "contradicted", "label": "Contradicted", "order": 0}, "..."],
  "defaultMarks": {"contradicted": "...", "no-clear-sign": "...", "emerging": "...", "supported": "...", "established": "..."},
  "lists": {
    "laborPricedBasket": {"version": "1.0", "pinned": "2026-10-06", "members": [{"name": "Accenture", "ticker": "ACN", "exchange": "NYSE"}]},
    "seatVendors": {"version": "1.0", "pinned": "2026-10-06", "members": ["..."]}
  },
  "claims": [
    {
      "id": "J3",
      "label": "Entry-level knowledge work goes first",
      "wording": "...",
      "why": "...",
      "lens": "work",
      "marks": {"contradicted": "...", "emerging": "...", "supported": "...", "established": "..."},
      "indicators": [
        {
          "id": "J3-nyfed",
          "name": "Recent-graduate unemployment against all workers",
          "source": "Federal Reserve Bank of New York, The Labor Market for Recent College Graduates",
          "url": "https://...",
          "cadence": "quarterly",
          "dataKind": "official",
          "series": null,
          "confounders": ["the rate cycle", "the unwinding of 2021-22 tech over-hiring"],
          "comparison": "all workers aged 22-65",
          "alsoBears": []
        }
      ],
      "status": "emerging",
      "since": "2026-10-08",
      "pending": null,
      "history": [{"date": "2026-10-08", "from": null, "to": "emerging", "why": "...", "evidence": ["2026-10-08#e4"], "by": "run"}]
    }
  ]
}
```

Rules:

- `wording`, `marks`, `indicators` and `lists` change only with a version bump and a dated `changelog` entry, and only on the owner's say-so. A run never edits them.
- A run may change only `status`, `since`, `pending` and append to `history`. `history` is append-only.
- `dataKind` is `official` (a government statistical agency, a regulator, a court, a market operator, a company's own filing) or `private` (payroll processors, job boards, consultancies, research using private data). Private data often leads official data by months; official data gets revised. Every number says which it is.
- `series` lists the pinned series ids fetched by `fetch_series.py` (for example `fred:DFII10`), or null when the indicator is read by the research agents.
- `alsoBears` names other claims an indicator speaks to (for example the J3 supply-side indicator also bears on J5 and J10).
- `pending` is null or `{"to", "since", "why", "evidence"}` for a move to Established or Contradicted awaiting the owner.

### 4.2 `editions/YYYY-MM-DD.json`

```json
{
  "schema": 1,
  "date": "2026-10-15",
  "claimsVersion": "1.0",
  "baseline": false,
  "window": {"from": "2026-10-09", "to": "2026-10-15"},
  "headline": "...",
  "dek": "...",
  "strip": [{"id": "J0", "status": "no-clear-sign", "prev": "no-clear-sign", "pending": null}],
  "moves": [{"id": "J3", "from": "no-clear-sign", "to": "emerging", "why": "...", "evidence": ["e4", "e7"], "by": "run"}],
  "pendingOwner": [{"id": "J4", "from": "supported", "to": "established", "why": "...", "evidence": ["e2"]}],
  "evidence": [
    {
      "id": "e4",
      "text": "...",
      "eventDate": "2026-10-13",
      "background": false,
      "url": "https://...",
      "otherUrls": [],
      "via": null,
      "rating": "verified fact",
      "ratingQual": null,
      "ratingNote": null,
      "kind": "official-series",
      "dataKind": "official",
      "bears": [{"claim": "J3", "direction": "for"}],
      "confounder": "...",
      "top": true
    }
  ],
  "nullCase": {"text": "...", "evidence": ["e9"]},
  "releases": [{"series": "bls:JTS510000000000000HIR", "period": "2026-08", "released": "2026-10-14", "value": 0.0, "note": "..."}],
  "gaps": [],
  "corrections": [{"date": "2026-10-15", "page": "jobs.html", "item": "...", "was": "...", "now": "...", "url": "https://..."}]
}
```

Rules:

- `headline` is at most 90 characters; `dek` at most 60 words.
- `strip` has all thirteen claims in id order. `prev` is the status in the previous edition (null in the baseline).
- `moves` lists status changes applied this week, at most one step each unless `by` is `owner`. Moves confirmed by the owner since the last edition appear here with `by: "owner"`.
- `pendingOwner` lists proposed moves to Established or Contradicted, not applied.
- `rating` is one of the six newsletter ratings (section 6), with the same `ratingQual` and `ratingNote` semantics.
- `kind` is one of `official-series`, `filing`, `company-statement`, `research`, `press`, `court`, `regulator`, `market-data`.
- `bears` lists every claim the item speaks to, each `for` or `against`.
- `nullCase` is always present: either `{"text", "evidence"}` with the week's strongest evidence for J0, or `{"none": "<reason>"}`.
- `releases` lists the scheduled series that came out in the window, from `series/releases.json`.
- `corrections` use the newsletter's corrections fields (`date`, `page`, `item`, `was`, `now`, `url`); the import adds `emailed: null` and `section: "jobs"`.
- A published edition (one committed and pushed) is frozen. A mistake is fixed by a correction in a later edition, never by editing the old one.

## 5. The claims

### 5.1 Default marks

Every claim's marks follow these defaults, made concrete per claim below.

| Status | Default mark |
|---|---|
| Contradicted | The main indicators move against the claim in at least two independent sources, sustained across two releases. |
| No clear sign | The indicators are flat or mixed, stay inside their pre-2022 range, or a named confounder fully explains them. This is the default when no other mark is met. |
| Emerging | One primary indicator moves the claim's way beyond its pre-2022 range or its comparison group, with the confounders examined and found insufficient. |
| Supported | Two independent indicators of different kinds agree (for example an official series and company disclosures), sustained across two releases. |
| Established | Supported for two quarters, visible in official statistics and not only private data, with no live alternative explanation. |

"A release" is one publication of the indicator at its own cadence (one monthly JOLTS release, one quarterly filing, one weekly LSAC update). For an event-driven indicator (statements, deals, rulings, filings of new forms), "two releases" means qualifying events in two different calendar months. "Two quarters" is calendar time, 182 days.

### 5.2 Move rules

1. A claim moves at most one step per edition. A bigger jump needs the owner.
2. A move to Established or Contradicted is recorded as `pending` and in `pendingOwner`; it takes effect only when the owner confirms it with `confirm.py`.
3. If a move rested on evidence later retracted, the claim drops back at once (not limited to one step) and the edition carries a correction.
4. A claim can't move on a stale series: if `fetch_series.py` failed for a series the move depends on, the move waits.
5. Downward moves follow the same marks: a claim drops when the evidence no longer meets its current mark.
6. The baseline edition sets each claim's starting status from the evidence that already exists (any date, background items labelled), with reasons and a `history` row whose `from` is null. It shows no arrows. The one-step limit doesn't apply to the baseline, but rule 2 does: a claim whose evidence meets Established starts at Supported, and one that meets Contradicted starts at No clear sign, each with the extreme recorded as `pending` for the owner.
7. J0 can stand at Supported or above while J2 or J3 does too: firm-level substitution can be real before it shows in aggregates. When that happens, the edition must say how the two fit together.

### 5.3 Pinned lists (claims.json v1.0)

Pinned lists stop us choosing examples after the fact. Each is versioned; a change is a claims version bump. Members are confirmed against the companies' own investor pages while writing `claims.json`; a member that can't be confirmed is dropped, not guessed.

- **laborPricedBasket** (J1): businesses whose revenue is mostly the sale of human labor. Accenture (ACN), Cognizant (CTSH), EPAM Systems (EPAM), Infosys (INFY), Wipro (WIT), Concentrix (CNXC), TTEC Holdings (TTEC), Teleperformance (TEP, Euronext Paris), Robert Half (RHI), ManpowerGroup (MAN). Comparison: the S&P 500 equal-weight index.
- **seatVendors** (J2, J8): software priced per seat or per employee. Salesforce, ServiceNow, Workday, Adobe, Atlassian, HubSpot, Zoom, monday.com.
- **offshoreServices** (J2): Tata Consultancy Services, Infosys, Wipro, HCLTech, Tech Mahindra (quarterly headcount); Concentrix and Teleperformance (headcount in annual reports); the Philippine IT-BPM industry body's annual headcount.
- **revenuePerEmployee** (J2): the seatVendors, the offshoreServices firms, Alphabet, Amazon, Apple, Meta, Microsoft, and the ten largest US banks by assets as of 2026-10-01. Revenue and headcount from SEC filings (XBRL where available).

### 5.4 Lenses

| Lens | Claims |
|---|---|
| capital | J1, J8, J9 |
| work | J2, J3, J6 |
| prices | J5, J10 |
| buyers | J4, J11 |
| policy | J7, J12 |
| null | J0 |

### 5.5 The thirteen claims

For each claim: the wording, why it's tracked, the indicators (source · cadence · data kind; confounders; comparison), and the marks that differ from the defaults. Sources named here are candidates: each is opened and confirmed while writing `claims.json`, and one that can't be confirmed is dropped, not replaced by a guess. Series ids are pinned the same way, after checking each exists on its publisher's site.

#### J0 · The null: so far, a normal technology transition

- **Wording:** So far, AI's effect on work stays within the range of past technology transitions: aggregate employment, wages and the pace of occupational change look like earlier waves, and gaps between AI-exposed and less-exposed work are small or explained by other causes.
- **Why:** the tracker's control. Without it, the tracker would only find what it looks for. Every edition reports the week's strongest evidence for it.
- **Indicators:**
  - Pace of occupational change against past tech waves (Yale Budget Lab's AI labor-market tracking, built on the Current Population Survey) · roughly monthly · official data, research analysis. Confounders: survey noise, the pandemic's distortions. Comparison: the 1980s-2000s computer and internet waves.
  - Prime-age employment-population ratio (BLS CPS) · monthly · official. Confounders: the business cycle.
  - Unemployment in AI-exposed against less-exposed occupations (CPS-based research from Federal Reserve banks and others) · irregular · official data, research analysis. Confounders: exposure measures differ between studies.
  - Labor productivity growth (BLS, nonfarm business) · quarterly · official. A break far above trend cuts against the null.
  - Wage growth by occupation or industry (Atlanta Fed Wage Growth Tracker) · monthly · official.
- **Marks:** Emerging: one primary source with at least twelve months of post-2022 data finds no differential effect beyond past waves. Supported: two sources of different kinds agree, across two releases. Established: Supported for two quarters in official data. Contradicted: AI-exposed work diverges from less-exposed work beyond past-wave ranges in two independent official-data sources across two releases.

#### J1 · Capital is already pricing in labor substitution

- **Wording:** Investors are already rewarding companies for replacing labor with AI and marking down businesses whose value rests on selling human labor, before the effects show in employment data.
- **Why:** the core of the section. Markets are forward-looking; their positioning is the earliest evidence of what they expect AI to do to work.
- **Indicators:**
  - The laborPricedBasket's price and trailing price/earnings against the S&P 500 equal-weight index · daily prices, quarterly earnings · market data (prices from a keyless public daily price endpoint chosen during implementation; earnings from SEC XBRL), computed by `fetch_series.py`. Confounders: interest rates, earnings changes, sector rotation. If no keyless price source proves reliable, this indicator is dropped from v1 and J1 runs on the others.
  - Market reactions to named AI-linked headcount announcements (announcement-day moves against the market, and earnings-call reception) · event-driven · market data and company statements. Confounders: other news on the same day, especially earnings.
  - AI and headcount language in earnings calls (transcripts; counts published by data providers such as FactSet) · quarterly · private. Confounders: hype; mentions are not actions.
  - Share of venture funding going to AI companies (PitchBook, Crunchbase reports) · quarterly · private. Confounders: the funding cycle.
  - Long-run real interest rates (10-year TIPS yield, FRED) · daily · official. Reported as a test of the strong form (markets pricing transformative growth); not required for any mark. Confounders: monetary policy, deficits, the inflation risk premium.
- **Marks:** Emerging: one primary indicator, either the basket derating against the comparison beyond what its earnings changes explain, or positive market reactions to AI-linked headcount cuts at several named firms within a quarter. Supported: two kinds agree across two releases. Established: Supported for two quarters, with capital allocation (venture share, capex) moving the same way. Contradicted: the basket re-rates against the comparison and AI-linked headcount cuts draw negative reactions, in two sources across two releases.

#### J2 · Firms cut hiring for AI before AI can do the whole job

- **Wording:** Companies are freezing or shrinking headcount and naming AI as the reason, while AI still can't do the whole job; output per worker rises.
- **Why:** this is how capital's expectation (J1) becomes a labor-market fact.
- **Indicators:**
  - Named company statements tying hiring freezes or cuts to AI (CEO memos, earnings calls, filings) · event-driven · company statements. Confounders: AI as a cover story for cuts made for cost or over-hiring reasons ("AI-washing"); statements alone never meet a mark without headcount data.
  - Challenger, Gray & Christmas job-cut reports, cuts attributed to AI · monthly · private. Confounders: the reason is self-reported.
  - WARN layoff notices (state labor departments) · continuous · official. Confounders: notices rarely give a reason.
  - Revenue per employee at the pinned revenuePerEmployee firms (SEC filings) · quarterly or annual · official. Confounders: price increases, acquisitions, outsourcing.
  - Seat and retention disclosures at the pinned seatVendors (paid seats where published, net revenue retention, renewal and attrition rates, management comments on customer headcount; Workday's pricing scales with customers' employee counts) paired with hyperscalers' disclosed token or inference volumes · quarterly · company statements. Confounders: vendors deliberately moving from per-seat to per-agent and per-outcome pricing; downturn spending cuts; vendor consolidation; trimming unused seats. Falling seats with rising tokens is consistent with payroll moving to compute; it is never proof on its own.
  - Quarterly headcount at the pinned offshoreServices firms, and the Philippine IT-BPM industry headcount · quarterly and annual · company filings and an industry body. Confounders: demand in client industries, pricing pressure, visa and trade policy.
  - JOLTS hires rate and quits rate, tracked separately, for Information and for Professional and business services, against less-exposed industries (for example Construction, Health care and social assistance, Leisure and hospitality) · monthly, 3-month averages · official. Confounders: the rate cycle (handled by the comparison), sample noise, revisions.
  - Freelance platforms: Upwork and Fiverr filings (active clients or buyers, spend per client, category mix) and academic studies run on platform data · quarterly and irregular · company filings and research. Confounders: post-pandemic normalization; both platforms remaking themselves as AI companies (their own restructurings are J2 data points).
- **Marks:** Emerging: one primary indicator, either repeated named statements from large firms tying cuts to AI with headcount data confirming the cuts, or the exposed industries' JOLTS hires rate falling below the comparison group beyond its pre-2022 range. Supported: firm evidence (statements with headcount or seat data) and an official series (JOLTS comparison or offshore headcount) agree across two releases. Established: Supported for two quarters, visible in official industry data against the comparison, with revenue per employee rising at the pinned firms and AI-washing examined and ruled out. Contradicted: firms that cited AI reverse or rehire and exposed-industry hiring keeps pace with the comparison, in two sources across two releases.

#### J3 · Entry-level knowledge work goes first

- **Wording:** The first jobs AI displaces are entry-level knowledge-work jobs: young workers in AI-exposed occupations lose ground to their peers in less-exposed work, and firms shrink graduate intake.
- **Why:** entry-level work is the most automatable part of most knowledge jobs, and cutting juniors is also a bet: a firm that stops hiring juniors is betting it won't need as many seniors in about ten years.
- **Indicators:**
  - Employment of 22-25-year-olds in AI-exposed against less-exposed occupations (research on ADP payroll data, such as Stanford Digital Economy Lab's "Canaries in the Coal Mine") · irregular · private data, research analysis. Confounders: the rate cycle, the tech over-hiring unwind.
  - Recent-graduate unemployment against all workers (New York Fed) · quarterly · official data. Confounders: the rate cycle.
  - Junior and entry-level postings, and postings in exposed against less-exposed categories (Indeed Hiring Lab, which publishes its postings data openly) · daily data, irregular reports · private. Confounders: postings are not hires; job-board coverage changes.
  - Graduate intake at the Big Four and large law firms (firm announcements; NALP) · annual · company statements and an industry body. Confounders: demand for audit and legal work; offshoring.
  - Supply side: college majors (National Student Clearinghouse; Computing Research Association), and exam and application volumes (LSAC weekly applicant volume, NCBE bar-exam statistics, NCSBN NCLEX counts, AICPA/NASBA CPA candidates), each against its pre-2022 trend · weekly to annual · official and industry bodies. Confounders: the CPA 150-hour rule and exam changes; counter-cyclical moves into graduate school in a weak job market. Also bears on J5 and J10: moves into licensed professions bet on the accountability moat, moves into nursing and trades bet on J5's physical moat and on J10; moves out of computer science are the J3 signal.
- **Marks:** Emerging: one primary dataset shows young workers in exposed jobs falling relative to the comparison group, beyond the pre-2022 range. Supported: two independent datasets (payroll research and postings, or the New York Fed series) show it across two releases. Established: Supported for two quarters, visible in BLS data, with the comparison group ruling out the rate cycle. Contradicted: young workers in exposed jobs keep pace with the comparison group in two sources across two releases.

#### J4 · Value moves to the physical bottlenecks

- **Wording:** As cognition gets cheap, the scarce physical inputs (electric power, grid capacity, chips, land with power and water, and materials such as copper) capture a growing share of the value, and their owners gain pricing power.
- **Why:** if cognitive labor stops being the bottleneck, the next bottlenecks are physical, and capital is already moving there.
- **Indicators:**
  - Data-center power deals: purchase agreements, nuclear restarts and new plants tied to AI load (company announcements; regulatory filings) · event-driven · company statements and official filings.
  - Capacity market prices and large-load tariffs (PJM capacity auction results; state utility commission dockets) · annual and event-driven · official and market operator. Comparison: regions without data-center clusters.
  - Interconnection queues: volume and wait times (Lawrence Berkeley National Laboratory's annual queue report; grid operators) · annual · research and official.
  - Equipment lead times: transformers and gas turbines (industry reports; turbine makers' backlogs) · quarterly · private and company filings.
  - Retail electricity prices (EIA; BLS average price data) and copper (global copper price, FRED) · monthly · official.
  - Bottleneck owners' margins and pricing: chip foundry gross margins, data-center vacancy and rents, utilities' allowed returns · quarterly · company filings, private, official.
  - Big Tech capex is not repeated here: the section links to the newsletter's "Follow the money".
- **Confounders:** general inflation, natural gas prices, weather, tariffs on metals, electrification unrelated to AI (vehicles, reshoring).
- **Marks:** Emerging: one primary indicator, for example capacity or retail power prices in data-center regions rising faster than in comparison regions, attributed by the grid operator or regulator to data-center load. Supported: prices or auctions and lead times or margins agree across two releases. Established: Supported for two quarters in official data, with bottleneck owners' margins rising beyond inflation. Contradicted: bottleneck prices and lead times ease as supply catches up and margins compress, in two sources across two releases.

#### J5 · The human moats hold, for now

- **Wording:** Work protected by dexterity in messy physical settings, by legal accountability (a human who signs and can be held liable) or by the value of human presence keeps its jobs and pay while AI-exposed work weakens.
- **Why:** these are the jobs that are supposed to be left. "For now" is the point: the tracker watches the clocks that would end each moat.
- **Indicators:**
  - Pay in the trades against all private-sector workers (BLS average hourly earnings, construction and specialty trades) · monthly · official. Confounders: the construction cycle, immigration policy.
  - Registered apprenticeships (Department of Labor) · annual · official.
  - The physical-automation clock: humanoid robot deployments (pilots against paid production units) and unit costs; industrial robot installations (International Federation of Robotics); robotaxi scale (paid rides per week, cities served) · quarterly to annual · company statements and an industry body. Fast growth here is evidence against J5.
  - Rules that keep or remove a licensed human's responsibility: laws, regulations and court rulings · event-driven · official. Also bears on J12.
  - Care work: employment and pay in home health, hospice and childcare (BLS) · monthly · official. Confounder: an ageing population raises care demand regardless of AI.
  - The J3 supply-side indicator (moves into trades and licensed professions).
- **Marks:** Emerging: one official series shows protected work's pay or employment beating the AI-exposed comparison beyond the pre-2022 range. Supported: pay or employment and the robot clock agree (protected work holding while deployments stay at pilot scale) across two releases. Established: Supported for two quarters in official data, with no scaled substitution in the robot clock. Contradicted: scaled robot deployments in trades or driving, or removal of human-signature requirements, with protected occupations' employment or pay falling against the comparison, in two sources across two releases.

#### J6 · New AI-era jobs are real but small

- **Wording:** AI creates new kinds of paid work (expert data work for model training, evaluation and red-teaming, AI operations, fleet and robot operations, provenance and verification), but the numbers stay small next to the work lost in J2 and J3.
- **Why:** "new jobs will appear" is the standard answer to automation; this claim tests whether they appear at a scale that matters.
- **Indicators:**
  - Postings mentioning AI roles and skills (Indeed Hiring Lab's AI tracking; LinkedIn Economic Graph) · monthly · private.
  - Expert data work: contractor counts and pay at firms that hire professionals to train and evaluate models (company statements and credible reports) · irregular · company statements and press. Confounders: labs' spending cycles; these firms promoting themselves.
  - New occupations becoming visible in official data (BLS Occupational Employment and Wage Statistics) · annual · official.
  - Estimates of roles created against roles lost (research) · irregular · research.
- **Marks:** "Small" means at least an order of magnitude below the losses measured under J2 and J3 over the same period. Emerging: one source shows new AI-era roles growing at that small scale. Supported: two sources of different kinds across two releases. Established: Supported for two quarters, with the roles visible in official data. Contradicted: new AI-era roles reach the same order of magnitude as the losses, in two sources across two releases.

#### J7 · Policy starts separating income from work

- **Wording:** Governments begin to pay income that isn't tied to work, citing AI: guaranteed income, AI dividends or public stakes in AI capital, and automation or compute taxes that fund transfers.
- **Why:** if labor stops being the main way income is distributed, policy has to replace it; the first moves show which way societies choose.
- **Indicators:**
  - Guaranteed-income pilots and programs, especially any justified by automation (Stanford Basic Income Lab's tracking; government sites) · irregular · official and research.
  - Bills and official proposals for AI dividends, sovereign wealth funds or public equity in AI firms (Congress, state legislatures, other countries' parliaments), by stage: proposed, advanced, enacted · event-driven · official.
  - Automation, robot or compute taxes proposed or enacted · event-driven · official.
  - AI-justified transition payments or extended unemployment insurance · event-driven · official.
- **Confounders:** guaranteed-income pilots motivated by poverty rather than AI; public stakes motivated by industrial policy.
- **Note:** human-in-the-loop mandates (rules that keep human roles for employment's sake) are resistance, not income separation; they are tracked under J12.
- **Marks:** Emerging: one enacted measure, or a proposal advancing in a national legislature, explicitly justified by AI's effect on work. Supported: measures of two different kinds, or in two jurisdictions, across two quarters. Established: an enacted national program in a G20 country that pays income not tied to work and is justified by AI. Contradicted: such measures are rejected or repealed and governments answer AI with work-linked support instead (for example expanded work requirements), in two jurisdictions across two releases.

#### J8 · The capital bet runs ahead of the revenue

- **Wording:** AI investment is running well ahead of the revenue it earns, and it is financed in ways (circular deals, debt, off-balance-sheet vehicles, long depreciation lives) that would turn a disappointment into a financial shock and slow the transition.
- **Why:** J1 asks whether capital is positioning; J8 asks whether capital is right. An unwind would hit jobs from the other side.
- **Indicators:**
  - AI capex against AI revenue: capex from hyperscaler filings (the newsletter's money data) plus disclosed lab and neocloud spending, against disclosed lab revenue and hyperscalers' AI revenue figures · quarterly · company filings and statements.
  - Circular financing: chipmakers or clouds investing in customers that buy from them; equity-for-compute deals · event-driven · filings and company statements.
  - Data-center debt: bond issuance, private credit, special-purpose vehicles; credit spreads on AI-linked borrowers · event-driven and daily · filings and market data.
  - Useful-life assumptions for servers and GPUs in hyperscalers' annual reports · annual · official filings.
  - Seat-revenue erosion at the pinned seatVendors against their agent and consumption revenue (the monetization half of the seat indicator) · quarterly · company statements.
- **Confounders:** infrastructure revenue lags capex by design; disclosures are selective; definitions of "AI revenue" vary by company. Past build-outs (railways, the 1998-2001 fiber boom) are framing only, carried as "our inference".
- **Marks:** Emerging: one primary indicator, for example the disclosed AI-revenue-to-capex ratio falling, or a material circular or off-balance-sheet financing disclosed in filings. Supported: a widening revenue gap and growing financing structures (or widening spreads) agree across two quarters. Established: Supported for two quarters in filings, plus a market signal (widening spreads on AI-linked debt, or depreciation lives shortened under audit pressure). Contradicted: AI revenue grows faster than AI capex for two quarters across two sources, and financing shifts to operating cash flow.

#### J9 · The gains go to owners, not wage earners

- **Wording:** The income AI creates flows mainly to owners of capital and a small group of top earners rather than to wages, so labor's share of income falls and spending comes to depend more on asset owners.
- **Why:** this is the end state of the thesis (demand depending on people without wages) in a form measurable now. The end state itself is framing on `jobs.html`, not a tracked claim.
- **Indicators:**
  - Labor share (BLS nonfarm business labor share; BEA compensation share of income) · quarterly · official. Confounders: the cycle, self-employment measurement, a long decline that predates AI.
  - Corporate profits as a share of GDP (BEA) · quarterly · official.
  - Top 10% and top 1% shares of household wealth and of corporate equities (Federal Reserve Distributional Financial Accounts) · quarterly · official.
  - Top-decile share of consumer spending (estimates built on Federal Reserve data, such as Moody's Analytics'; the BLS Consumer Expenditure Survey) · quarterly and annual · private and official.
  - Market concentration: the share of US market value in the ten largest companies · daily · market data, computed.
  - Pay for top AI researchers (disclosed and credibly reported packages) · event-driven · press.
  - Evidence against: falling prices per unit of AI capability (Epoch AI's price data) and open-weight models matching closed ones, which would mean users capture the gains · irregular · research.
- **Marks:** Emerging: one official series moves the claim's way beyond its pre-2022 trend. Supported: labor share (or compensation share) and a wealth or spending concentration measure agree across two releases. Established: Supported for two quarters in official data, not offset by consumer-capture evidence. Contradicted: labor share rises, or falling prices pass the gains to users broadly, in two sources across two releases.

#### J10 · Spending and jobs shift to what AI can't make cheap

- **Wording:** Prices of services AI can do fall relative to services that need people (healthcare, education, childcare, housing and the trades), and those human-heavy sectors take a growing share of spending and jobs (Baumol's cost disease).
- **Why:** this is the main way most economic models say jobs move, and the economic (not only technical) reason the J5 moats exist.
- **Indicators:**
  - CPI for AI-exposed services (for example legal services, tax preparation and accounting, computer software) against human-intensive services (medical care services, day care and preschool, tuition, rent) · monthly · official. Confounder: Baumol's effect predates AI, so the test is a change in the gap against its pre-2022 trend.
  - Employment shares: health care and social assistance, education, construction, against information and professional and business services (BLS) · monthly · official. Confounder: ageing raises care employment regardless.
  - Personal consumption shares by category (BEA) · monthly · official.
  - The J3 supply-side indicator (moves into nursing and trades).
- **Marks:** Emerging: one official series breaks from its pre-2022 trend the claim's way. Supported: the price gap and job shares both move the claim's way across two releases. Established: Supported for two quarters, with consumption shares moving too. Contradicted: exposed services prices don't fall against the trend and human-heavy sectors' job shares stall, in two sources across two releases.

#### J11 · The customer becomes an agent

- **Wording:** Searching, buying and paying increasingly go through AI agents, and businesses rebuild marketing, media, retail and payments for machine customers.
- **Why:** businesses are positioning for AI buyers as well as AI workers; that changes which jobs exist in marketing, media and retail.
- **Indicators:**
  - Agent payment rails launched and used (payment networks' and processors' agent protocols), with disclosed volumes · event-driven and quarterly · company statements.
  - Publishers' search referral traffic and click-through when AI answers appear (Pew Research Center; traffic analytics firms; publishers' own disclosures) · irregular · research and private.
  - Search advertising against AI-answer advertising; agencies restructuring · quarterly · company filings.
  - AI-referred retail traffic and orders (retail analytics reports; retailers' disclosures) · irregular · private and company statements.
  - Media and marketing job cuts tied to AI search and agents (shared with J2) · event-driven · company statements.
- **Confounders:** launches without use (an announced protocol is not adoption); traffic-measurement methods; search algorithm changes unrelated to AI answers.
- **Marks:** Emerging: one primary indicator, a disclosed volume through agent rails or a measured fall in publisher referrals attributable to AI answers. Supported: adoption (volumes) and a business response (restructuring, referral losses) agree across two releases. Established: Supported for two quarters, with large platforms disclosing a material agent-mediated share of transactions or traffic. Contradicted: agent rails see little use and referral traffic stabilizes, in two sources across two releases.

#### J12 · Backlash becomes a brake

- **Wording:** Resistance from workers, communities, courts, insurers and voters measurably slows the use of AI at work, through contracts, local denials, liability, insurance terms and law.
- **Why:** the pace of the transition may be set less by capability than by what institutions allow. Insurance and liability are often a faster, harder brake than legislation.
- **Indicators:**
  - Union contracts with AI clauses; strikes over automation (BLS major work stoppages; union announcements) · event-driven · official and statements.
  - Data-center projects delayed, denied or under moratorium; large-load tariffs that shield households; power bills as a political issue (local government records, state utility commission dockets, trackers of local opposition) · event-driven · official and private.
  - Laws restricting AI in hiring, firing and management, and mandated human roles (human-in-the-loop requirements) · event-driven · official. Federal pre-emption of state AI laws counts against J12.
  - Insurance: AI exclusions in errors-and-omissions and general liability policies (state form filings; standard endorsement forms), cyber underwriting surcharges for AI use; and, as evidence against, insurers writing affirmative AI coverage · event-driven · official filings and company statements.
  - Court rulings on liability for AI agents and AI decisions (dockets) · event-driven · official. Also bears on J5.
  - Public opinion on AI and jobs (Pew Research Center, Gallup) · irregular · research.
- **Confounders:** projects delayed for ordinary reasons (financing, power availability); laws passed but delayed or unenforced; exclusions that clarify cover rather than remove it.
- **Marks:** Emerging: one primary indicator, for example an AI exclusion filed in several states, or several data-center denials within a quarter attributed to opposition. Supported: two kinds (insurance or liability, and local or labor action) agree across two releases. Established: Supported for two quarters, with a measurable slowdown (deployments delayed or cancelled, firms citing liability or insurance as a reason not to deploy). Contradicted: the brake releases (affirmative coverage widely available, laws repealed or pre-empted, contested projects approved), in two sources across two releases.

## 6. Evidence rules

The newsletter's rules, adapted. The workflow carries them in its prompts; the newsletter's import validator enforces the parts that can be checked mechanically.

- **Ratings:** one closed set: verified fact · credible report · expert opinion · forecast aggregate · our inference · speculation, with the newsletter's meanings. "Verified fact" needs a primary source, or two independent credible outlets actually opened, each stating it as its own claim. Our own reasoning (including every "consistent with" reading of an indicator) is "our inference". An item mixing a fact with our reading keeps "verified fact" only with the qualifier "(part our inference)".
- **Attribution:** a statement quoted by an outlet is rated as the speaker's statement, with "via" naming the outlet.
- **Dates:** each item is dated by when the event happened. Items older than the window are marked `background`.
- **Official series and market prices** come only from `fetch_series.py` output, never from press coverage of them.
- **Confounders:** an item that could move a claim names the confounder that applies, or says why none does.
- **No single item moves a claim.** Marks need agreement across indicators as written.
- **Denylist:** never cite the aggregator domains the newsletter denylists (`DENYLIST` in the newsletter's `scripts/check_data.py`); the import refuses an edition that does.
- **No investment language:** no buy, sell or hold, no price targets.
- **Voice:** first person plural, plain verbs, "a custom AI agent" as the author, as on the rest of the site.

## 7. The Thursday run

### 7.1 The routine (`jobs-weekly` scheduled task)

A local scheduled task like `daily-agi-assessment` and `weekly-agi-wrapup`, Thursdays at about 19:07 Pacific, working in `/Users/joeldg/Projects/post_agi_work`. Creating it is persistent configuration, so it is created only with the owner's approval. Its first scheduled run is the first Thursday at least five days after the baseline edition.

0. **Preflight.**
   - DATE is today's Pacific date, which must be a Thursday. On any other day the scheduled run reports the missed run in one line and stops. A manual rerun is the owner's call: run by hand with an explicit DATE (the Thursday), it is accepted until 11:00 PT the next day and must finish by then. The baseline (section 11) is also run by hand, with `baseline: true` and any date.
   - If `editions/<DATE>.json` exists, stop: duplicate.
   - `git pull --ff-only`; stop if refused. Stop if `claims.json`, `editions/`, `series/` or `scripts/` have uncommitted changes.
   - **Usage valve:** load the usage tool and skip the run (no edition this week, owner notified) if the 5-hour window is at 70% or more, or any weekly window is at 75% or more. These sit below the daily and wrap-up's lean thresholds (85% and 92%) so a Jobs run can't push Friday's runs onto their lean paths. The thresholds are revisited after the rehearsal measures what a run uses.
1. `python3 scripts/fetch_series.py` (writes `series/` and `series/releases.json`).
2. The `jobs-weekly` workflow (7.2), with args `{"date": DATE}`.
3. `python3 scripts/check_plugin.py`; must exit 0.
4. Commit explicit paths only (`editions/<DATE>.json`, `claims.json`, `series/`), never `git add -A`, then `git push origin main`.
5. Push notification: the headline, the moves, any `pendingOwner` items awaiting confirmation (with the `confirm.py` command), any unconfirmed items from earlier weeks, and gaps.
6. Final output, then stop.

**Deadlines:** the target is committed by about midnight Pacific. Anything uncommitted at 06:00 PT Friday is restored (`git checkout --` on tracked paths, removal of untracked files this run created) and the owner notified: no edition that week.

**Failure:** if any step fails, nothing is committed, the tree is restored, and the owner is notified with the step and the error.

### 7.2 The workflow (`.claude/workflows/jobs-weekly.js`)

Same patterns as the newsletter's workflows: args as an object or its JSON text; `agentMax()` runs every agent on Claude Fable 5.1 (model `fable`) at effort max and retries a declined call once on the default model at max, logging the label in `fallbacks`; scratch under `.claude/work/jobs-<DATE>/` only.

**Args:** `date` (required), `baseline` (boolean, default false), `repo` (default `/Users/joeldg/Projects/post_agi_work`; a scratch copy for a rehearsal), `researchBy`, `writeBy` (Pacific HH:MM soft deadlines).

**Phases:**

1. **Research.** Six lenses in parallel (5.4). Each research agent reads `claims.json` (its claims' wording, marks, indicators and pinned lists), `series/releases.json` and the previous edition, searches the window (in baseline mode, the evidence base to date), opens every source it uses, and returns claims in a fixed schema: text, event date, URL, other URLs, kind, data kind, proposed rating, `bears` with direction, confounder, material flag. The null lens looks only for the strongest evidence that this is a normal technology transition, across all claims' areas.
2. **Verify.** As each lens lands, an adversarial verifier tries to break every item (assume it's wrong until the source proves it): verified, downgraded, refuted or unverifiable, with the final rating and "via". Only surviving items continue. Items that could move a claim get a second, independent refuter.
3. **Decide.** One agent applies each claim's marks and the move rules (5.2) to the verified items, the series and the claim's history, and proposes moves with reasons. A separate refuter tries to break each proposed move. Moves that survive are applied (one step at most); moves to Established or Contradicted go to `pendingOwner`.
4. **Write.** The writer writes `editions/<DATE>.json` and updates `claims.json` (`status`, `since`, `pending`, appended `history` rows only), then runs `python3 scripts/check_plugin.py` and fixes until it passes.
5. **Review.** A hostile reviewer checks sourcing, ratings, attribution, dates, named confounders, the null case, overclaiming ("proof", "shows that" on our inference), investment language, and that only the allowed `claims.json` fields changed. A fixer applies its findings and reruns `check_plugin.py`.

**Writes:** `editions/<DATE>.json`, `claims.json` (allowed fields only), scratch. Never commits, pushes or touches any other repo.

**Returns:** `{ready, headline, moves, pendingOwner, gaps, fallbacks, review}`.

### 7.3 `fetch_series.py`

- Reads every `series` id in `claims.json`, fetches each from its public endpoint (FRED's keyless CSV download, the BLS public API v1, SEC EDGAR XBRL with a User-Agent contact as the SEC requires, the chosen daily price endpoint), and writes `series/<id>.json` with the observations and the fetch time.
- Writes `series/releases.json`: observations that are new since the previous edition's date.
- A failed fetch keeps the last good file, marks the series `stale` in `releases.json`, and exits 0 with a warning line, so the run continues and the edition lists the gap. A malformed `claims.json` series id exits 2.
- Derived series (the basket's relative price and P/E, revenue per employee, market concentration) are computed here, never by an agent.

### 7.4 `check_plugin.py`

Read-only. Exits 0 when all pass, 1 on any failure (naming the file, field and rule). Rules:

- `claims.json` and every edition parse; schema shapes and required fields.
- Status ids on the scale; `strip` has all thirteen claims in order.
- Ratings in the closed set; `ratingQual` at most five words.
- URLs are http(s) and not on the denylist.
- Every move is one step, or `by: "owner"`; moves to Established or Contradicted only `by: "owner"`. In the baseline edition the one-step rule doesn't apply, but no claim may start at Established or Contradicted (5.2, rule 6).
- `history` is append-only and each row's `to` equals the next row's `from`; the last row matches `status`.
- `wording`, `marks`, `indicators` and `lists` unchanged since `HEAD` unless `version` and `changelog` changed with them.
- Committed editions unchanged since they were committed (frozen).
- `nullCase` present; `headline` and `dek` within their limits.
- Every evidence id referenced by moves and the null case exists.

### 7.5 `confirm.py`

`python3 scripts/confirm.py J3 --to established` or `python3 scripts/confirm.py J3 --reject`. Confirming applies the pending move with a `history` row (`by: "owner"`); rejecting clears `pending` with a `history` row whose `from` and `to` both equal the current status and whose `note` says which move was rejected. It refuses when no matching move is pending. It then commits `claims.json` locally ("Owner confirms J3: established" or "Owner rejects J3: established"), so the next Thursday's clean-tree check passes; it never pushes. The next run pushes that commit with its edition and reports the confirmation in `moves`.

## 8. The newsletter side

All on `redesign-v2` or a branch off it.

### 8.1 `scripts/import_jobs.py --date <FRIDAY>`

- Finds the plugin at `--plugin DIR`, else `$JOBS_PLUGIN`, else `../post_agi_work` relative to the repo root. The path is never written into public data.
- Reads only committed files: `git -C <plugin> show HEAD:<path>`.
- Picks the newest edition dated in the seven days up to and including the Friday.
- Validates it and `claims.json` with the newsletter's own `checks/jobs.py`, not the plugin's checker.
- Writes `data/jobs/<FRIDAY>.json` (the edition plus `"edition": "<Thursday date>"` and `"source": "post_agi_work@<short commit>"`) and `data/jobs/claims.json`.
- Appends the edition's corrections to `data/corrections.json` with `"emailed": null` and `"section": "jobs"`, so they reach `changes.html#corrections` and the next daily email's correction box like any other correction.
- Exit 0: imported. Exit 3: no plugin or no edition in the window (normal; the wrap-up carries on without Jobs). Exit 2: invalid, refused, with the reason (the wrap-up carries on without Jobs and says so). Running it again with the same inputs gives the same result.

### 8.2 The "Jobs" section in the wrap-up (`scripts/build_weekly.py`)

Rendered only when `data/jobs/<DATE>.json` exists, so every past wrap-up rebuilds byte for byte unchanged.

- **Page** (`weekly/<DATE>.html`): the last section, `id="jobs"`, header "Jobs", after the standard sections and before the frozen-data note. The headline and dek; a status strip of all thirteen claims with arrows on those that moved and "under review" on a pending extreme; the moves with reasons; the top evidence items with rating chips and sources; the null case; the week's data releases; "Full tracker →" to `../jobs.html`. In the baseline edition, "Starting statuses" instead of arrows.
- **Email:** after the section notes and before the closing links, at most 200 words: header "Jobs", the headline, each move in one sentence, one line for the null case, "Full tracker →". In a week with no moves: "No claim moved this week" and the top two or three evidence items. The email subject never changes.

### 8.3 `jobs.html` ("Jobs watch")

Generated by `scripts/build_pages.py` from `data/jobs/claims.json` and the newest `data/jobs/*.json`. Registered in `PAGES`; a child of the **"Today"** hub in `NAV` (alongside `archive.html` and the wrap-ups that carry it), with `CRUMB_TITLES["jobs.html"] = "Jobs watch"`. The owner approved "the money hub", but `money.html` is a child of "Could it be hidden?", which would misfile Jobs; the owner confirms "Today" at spec review.

Contents: a one-line glance (statuses at a count); an intro (what the tracker is, that it never feeds the Index, the odds or the alarm, the thesis and its end state as framing, and how to read the scale); the status board; each claim collapsed under its id (`#J0` to `#J12`) with its wording, marks, indicators (source, cadence, data kind, confounders, comparison) and history; the newest edition's evidence; an archive of editions, each linking to the wrap-up that carried it. The naming key on `start-here.html#names` gains one line for the Jobs scale.

### 8.4 Checks and tooling

- `scripts/checks/jobs.py`, run by `check_data.py`: the schema; the closed rating set; safe, non-denylisted URLs; statuses on the scale; one-step moves unless owner-confirmed; append-only `history`; published `data/jobs/<date>.json` frozen; claims wording, marks, indicators and lists changing only with a version bump and changelog entry.
- `smoke.py`: `jobs.html` at 375 and 1280 px, and its anchors `#J0` to `#J12`.
- `build_feed.py`: `jobs.html` in `STANDING_PAGES` (sitemap).
- `check_data.py --pages`: the Jobs email block's 200-word budget (warning).

### 8.5 Routine and docs

- **README** (newsletter): a "Jobs plugin" section (the contract, the paths, the exit codes), Layout rows for `data/jobs/`, `jobs.html` and `scripts/import_jobs.py`, and the wrap-up procedure's new step.
- **Private `weekly-agi-wrapup` task:** a new step after the updates and before `build_weekly.py`: run `import_jobs.py --date <DATE>` and record its exit code. Step 5's commit list gains `data/jobs/<DATE>.json`, `data/jobs/claims.json` and `jobs.html` when changed (and `data/corrections.json`, already listed). The final output gains one line: Jobs imported, skipped (no edition) or refused (reason). This change is made only after the redesign is live.
- **Plugin README:** the same contract from the plugin's side, the routine, `confirm.py`, and how to rehearse.

## 9. Failure handling

| What goes wrong | What happens |
|---|---|
| No plugin, or no edition this week | `import_jobs.py` exits 3; the wrap-up is exactly as it is today. |
| The edition fails validation | Exits 2, refused; the wrap-up goes out without Jobs; its final output and a push notification say why. |
| The Thursday run fails or overruns | Nothing is committed; the plugin tree is restored; the owner is notified. A manual rerun can be made until 11:00 PT Friday; after 06:00 Friday, unfinished work is discarded. |
| The usage valve trips | The run is skipped and the owner notified; no edition that week. |
| A data source is down | The last good series is kept and the gap goes in the edition; no move rests on a stale series. |
| A pending extreme is unconfirmed | It stays pending, shown as "under review"; each Thursday notification reminds the owner. |
| A published Jobs item is wrong | A correction in the next edition, appended to the newsletter's corrections log by the import. |
| The plugin's checkout is dirty on Friday | Irrelevant to the newsletter: the import reads the committed `HEAD` only. |

## 10. Testing

Standard-library `unittest` with fixtures, like the newsletter.

- **Plugin:**
  - `check_plugin.py`: one passing base fixture and one failing fixture per rule (a rating off the set, a two-step move not confirmed by the owner, an edited `history` row, an edited committed edition, a missing null case, an indicator without confounders, an unknown series id, a claims wording change without a version bump, a dangling evidence id).
  - `fetch_series.py` on saved responses (no network in tests), including a failed fetch keeping the last good file.
  - `confirm.py`: confirm, reject, refuse when nothing is pending.
- **Newsletter:**
  - `test_import_jobs.py`: exit codes 0, 2 and 3; the seven-day window; reading from `HEAD` only (an uncommitted edition is ignored); corrections appended once; reruns give the same result.
  - `build_weekly` tests: without a Jobs file, output is byte-identical to the current output (guarding frozen wrap-ups); with one, the section on the page and in the email, including the baseline and no-moves variants.
  - `checks/jobs.py`: failing fixtures per rule, in the newsletter's `fixtures/checks/` style.
  - `smoke.py` covering `jobs.html`.
- **Rehearsal:** one full workflow run into a scratch copy of the plugin repo (`repo` arg), then an import and wrap-up build in a newsletter worktree, with nothing committed or sent. It measures the run's usage for the valve thresholds.

## 11. Rollout

1. Build the plugin repo's scaffolding and write `claims.json` v1.0: all thirteen claims, marks, indicators with confirmed sources and series ids, and the pinned lists. **The owner's review of `claims.json` is the editorial sign-off.**
2. `fetch_series.py`, `check_plugin.py`, `confirm.py` and their tests.
3. The `jobs-weekly` workflow, and a rehearsal run.
4. **The baseline.** A full run with `baseline: true`, dated the day it runs, then `check_plugin.py`, and everything committed and pushed to `joeldg/post_agi_work` (owner's instruction, 2026-10-06: "do a full run and commit everything ... so we start at a baseline").
5. Create the Thursday routine (with the owner's approval).
6. The newsletter side on `redesign-v2`: `import_jobs.py`, the wrap-up section, `jobs.html`, the checks and tests, the README.
7. After the redesign is live: update the private wrap-up routine. The first wrap-up to carry Jobs imports the newest edition in its week; earlier editions, the baseline included, appear in the `jobs.html` history and archive.

The plugin can run every Thursday before step 7: editions build up, and the owner can read them and calibrate the claims before anything is published in the newsletter.
