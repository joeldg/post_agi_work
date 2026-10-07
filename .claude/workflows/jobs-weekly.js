export const meta = {
  name: 'jobs-weekly',
  description: 'Jobs plugin weekly edition (Hidden AGI watch): six lenses researched then adversarially verified (Claude Opus 5.5 at effort xhigh), one decision under the published marks, a refuter per proposed move, a deterministic write through scripts/apply_edition.py, hostile review and fix. Writes editions/<date>.json and the allowed claims.json fields; never commits or pushes.',
  whenToUse: 'Run by the jobs-weekly routine (docs/routine.md) with args {date: "YYYY-MM-DD"}; the baseline with {date, baseline: true}. Optional: repo (a scratch copy, for a rehearsal), only (a list of lens keys, for a rehearsal), researchBy and writeBy (Pacific HH:MM soft deadlines). Every agent runs on Claude Opus 5.5 (model opus) at effort xhigh, the owner choice of 2026-10-06; a failed call is retried once.',
  phases: [
    { title: 'Preflight', detail: 'the run state from scripts/state.py' },
    { title: 'Research', detail: 'six lenses, each verified adversarially as soon as it lands; material items get a second refuter' },
    { title: 'Decide', detail: 'statuses under the published marks, then a refuter per proposed move' },
    { title: 'Write', detail: 'the edition and the claims update through scripts/apply_edition.py' },
    { title: 'Review', detail: 'hostile review, then a fixer' },
  ],
}

// ---------------------------------------------------------------- inputs
let A = args || {}
if (typeof A === 'string') {
  try { A = JSON.parse(A) } catch (e) { throw new Error('jobs-weekly: args is a string but not JSON. Pass {"date": "YYYY-MM-DD"} (optional baseline, repo, only, researchBy, writeBy)') }
}
const DATE = A.date
if (!DATE || !/^\d{4}-\d{2}-\d{2}$/.test(String(DATE))) throw new Error('jobs-weekly needs args.date = "YYYY-MM-DD" (the Pacific date of the run)')
const BASELINE = A.baseline === true
const REPO = A.repo || '/Users/joeldg/Projects/post_agi_work'
const ONLY = Array.isArray(A.only) && A.only.length ? A.only : null
const RESEARCH_BY = A.researchBy || '22:00'
const WRITE_BY = A.writeBy || '23:30'
const WORK = REPO + '/.claude/work/jobs-' + DATE
const EDITION = 'editions/' + DATE + '.json'

// Owner (2026-10-06): Jobs runs every agent on Claude Opus 5.5 at effort xhigh ("extra high"); Fable is not needed.
// A call that returns null or throws is retried once with the same prompt and options; its label goes in fallbacks.
const MODEL = 'opus'
const EFFORT = 'xhigh'
const fallbacks = []
async function runAgent(prompt, opts) {
  const o = Object.assign({}, opts || {}, { model: MODEL, effort: EFFORT })
  const label = o.label || 'agent'
  let out = null
  let why = 'returned null'
  try { out = await agent(prompt, o) } catch (e) { why = 'threw: ' + ((e && e.message) || String(e)) }
  if (out !== null && out !== undefined) return out
  log('Agent "' + label + '" ' + why + ': retrying once')
  fallbacks.push(label)
  return agent(prompt, o)
}

// ---------------------------------------------------------------- the scale (spec 4)
const STATUS = ['contradicted', 'no-clear-sign', 'emerging', 'supported', 'established']
const EXTREMES = ['contradicted', 'established']
const RATINGS = ['verified fact', 'credible report', 'expert opinion', 'forecast aggregate', 'our inference', 'speculation']
const KINDS = ['official-series', 'filing', 'company-statement', 'research', 'press', 'court', 'regulator', 'market-data']
const rank = s => STATUS.indexOf(s)
const stepToward = (from, to) => STATUS[rank(from) + Math.sign(rank(to) - rank(from))]
function dayAfter(d) {
  const t = new Date(d + 'T00:00:00Z')
  return new Date(t.getTime() + 86400000).toISOString().slice(0, 10)
}

// ---------------------------------------------------------------- shared prompt blocks
const GROUND = [
  'You are one stage of the Jobs plugin\'s ' + (BASELINE ? 'BASELINE run' : 'weekly run') + ' for ' + DATE + ' (Pacific). The Jobs plugin is a weekly thesis tracker on the transition to a post-AGI economy, published as the "Jobs" section of the Hidden AGI watch Friday wrap-up. Repo: ' + REPO + ' (run every command from the repo root). The design is docs/superpowers/specs/2026-10-06-jobs-plugin-design.md; claims.json holds the thirteen claims (J0-J12), their wording, marks (the rules for each status), indicators (source, cadence, data kind, confounders, comparison) and history.',
  'The core lens of the tracker: capital is forward-looking. Firms and markets act on what they expect AI to do before it shows in employment data, so their positioning is the earliest evidence. The tracker TRACKS claims; it never endorses them. Evidence against a claim matters as much as evidence for it.',
  'HARD LIMITS: no git commands that change anything (no add, commit, stash, checkout, reset, pull, push); edit only the files your stage names; any scratch file goes under ' + WORK + '/ only (mkdir -p it), never elsewhere in the repo. Never call api.bls.gov yourself (the series in series/ already hold the official numbers).',
  'Web: load the web tools with ToolSearch query "select:WebSearch,WebFetch"; curl via Bash is fine for plain GET requests to public pages and data files. Never use the in-app browser or Chrome tools (mcp__Claude_Browser__*, mcp__claude-in-chrome__*): this run is unattended and nobody can approve a site there. Open every source you rely on; never cite a page you did not open, and never invent a URL, date, number or quote. If a site blocks automated access with a CAPTCHA, browser challenge or human-verification check, do not try to get around it: use another source (a mirror such as GovTrack for congress.gov) or list it as blocked. To read a PDF, download it with curl into the scratch folder and open it with the Read tool (pages "1-20" at a time).',
  'Time: check the Pacific clock with TZ=America/Los_Angeles date +%H:%M. Research stops by ' + RESEARCH_BY + ' PT and writing is done by ' + WRITE_BY + ' PT; finish with honest gaps rather than overrun.',
].join('\n')

const EVIDENCE = [
  'EVIDENCE RULES (spec section 6; apply them exactly):',
  '- RATINGS, one closed set: verified fact · credible report · expert opinion · forecast aggregate · our inference · speculation. "verified fact" needs a primary source (a statistical agency, regulator, court, market operator, a company\'s own filing or statement for what the company says, a peer-reviewed or institutional study for what it found) or two independent credible outlets actually opened, each stating it as its own claim. A single report on anonymous sources, a leak or a "reportedly" item is "credible report". A named expert\'s or organisation\'s judgment is "expert opinion". A crowd or market figure is "forecast aggregate". Our own reasoning from the sources, including every "consistent with" reading of an indicator, is "our inference". A possibility no evidence supports is "speculation". An item mixing a fact with our reading keeps "verified fact" only with the qualifier "(part our inference)".',
  '- ATTRIBUTION: a statement quoted or relayed by an outlet is rated as the speaker\'s statement, with "via" naming the outlet ("a Salesforce executive, via Reuters"). Never show the outlet as the author of someone else\'s words.',
  '- DATES: date each item by when the event happened (or, for data, the period it measures), not the article date. Items older than the window are background.',
  '- OFFICIAL SERIES come only from the files in series/ (written by scripts/fetch_series.py): quote a value with its series id and observation date. Never take an official number from press coverage of it. The url for a series item is its public page (https://fred.stlouisfed.org/series/<ID> or https://data.bls.gov/timeseries/<ID>), never a data endpoint such as fredgraph.csv or api.bls.gov.',
  '- ITEM TEXT is what readers see: one or two complete sentences stating the finding, with its numbers, period and source. It stands alone: never refer to another item by an id (c3, e7), never address a later stage, never write instructions.',
  '- CONFOUNDERS: every item that could move a claim names the confounder that applies (from the claim\'s indicators in claims.json, or one you found), or says why none does. No single item moves a claim; the marks need agreement across indicators.',
  '- DENYLIST: never cite shattered.io, aitoolsreview.co.uk, geotoolbox.ai, aistop.watch or aiweekly.co; find the primary source instead.',
  '- NO INVESTMENT LANGUAGE: no buy, sell or hold, no price targets, no "investors should". Companies and markets are evidence, nothing more.',
  '- VOICE: plain verbs, first person plural ("we"), no dramatic words; never "proof", "proves" or "shows that" for our own inference.',
].join('\n')

const MARKS = [
  'THE MARKS (spec 5.1 and 5.2). The marks written in claims.json for each claim are the rule; quote the mark you apply.',
  '- Defaults: Contradicted = the main indicators move against the claim in at least two independent sources, sustained across two releases. No clear sign = flat or mixed, inside the pre-2022 range, or fully explained by a named confounder (the default when no other mark is met). Emerging = one primary indicator moves the claim\'s way beyond its pre-2022 range or its comparison group, confounders examined and insufficient. Supported = two independent indicators of different kinds agree, sustained across two releases. Established = Supported for two quarters (182 days), visible in official statistics and not only private data, with no live alternative explanation.',
  '- A release is one publication at the indicator\'s own cadence; for an event-driven indicator, "two releases" means qualifying events in two different calendar months.',
  '- Moves: at most one step per edition. A move to Established or Contradicted is never applied by a run: it is proposed for the owner (pending). A claim cannot move on a stale series. Downward moves follow the same marks.',
  BASELINE
    ? '- THIS IS THE BASELINE: set each claim\'s starting status from all the evidence that exists to date (background items labelled). The one-step limit does not apply, but no claim may start at Established or Contradicted: one whose evidence meets Established starts at Supported, one that meets Contradicted starts at No clear sign, each with the extreme proposed as pending for the owner.'
    : '- THIS IS A WEEKLY EDITION: each claim moves at most one step from its current status in claims.json, or stays.',
  '- J0 (the null) can stand at Supported or above while J2 or J3 does too (firm-level effects can be real before they show in aggregates); when that happens, say how the two fit together.',
].join('\n')

// ---------------------------------------------------------------- schemas
const S = { type: 'string' }
const SA = { type: 'array', items: { type: 'string' } }
const BEARS = { type: 'array', items: { type: 'object', properties: { claim: S, direction: { type: 'string', enum: ['for', 'against'] } }, required: ['claim', 'direction'] } }

const STATE = {
  type: 'object',
  properties: {
    date: S, claimsVersion: S,
    prev: { type: ['object', 'null'] },
    claims: { type: 'array', items: { type: 'object' } },
    ownerMoves: { type: 'array', items: { type: 'object' } },
    releases: { type: 'array', items: { type: 'object' } },
    stale: SA,
  },
  required: ['claimsVersion', 'prev', 'claims', 'ownerMoves', 'releases', 'stale'],
}

const FOUND = {
  type: 'object',
  properties: {
    lens: S,
    items: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: S, text: S, eventDate: S, background: { type: 'boolean' }, url: S, otherUrls: SA,
          kind: { type: 'string', enum: KINDS }, dataKind: { type: 'string', enum: ['official', 'private'] },
          proposedRating: { type: 'string', enum: RATINGS }, bears: BEARS, confounder: S,
          material: { type: 'boolean' }, why: S,
        },
        required: ['id', 'text', 'eventDate', 'url', 'kind', 'dataKind', 'proposedRating', 'bears', 'confounder', 'material'],
      },
    },
    blocked: SA,
    notes: S,
  },
  required: ['lens', 'items'],
}

const VERDICTS = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: S,
          verdict: { type: 'string', enum: ['verified', 'downgraded', 'refuted', 'unverifiable'] },
          rating: { type: 'string', enum: RATINGS.concat(['drop']) },
          ratingQual: S, ratingNote: S,
          correctedText: { type: 'string', description: 'The complete published text of the item with your corrections applied: one or two finished sentences stating the finding. Never instructions or notes. Empty when the original text stands.' },
          eventDate: S, url: S, via: S, evidence: S,
          notes: { type: 'string', description: 'Anything for later stages (what you checked, caveats). Never published.' },
        },
        required: ['id', 'verdict', 'rating', 'evidence'],
      },
    },
    notes: S,
  },
  required: ['results'],
}

const REFUTE = {
  type: 'object',
  properties: {
    results: { type: 'array', items: { type: 'object', properties: { id: S, refuted: { type: 'boolean' }, correctedText: { type: 'string', description: 'When the item survives but needs fixing: its complete published text with the fix applied, as finished sentences, never instructions. Empty otherwise.' }, evidence: S }, required: ['id', 'refuted', 'evidence'] } },
  },
  required: ['results'],
}

const DECISION = {
  type: 'object',
  properties: {
    headline: S,
    dek: S,
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: S,
          status: { type: 'string', enum: STATUS },
          pendingTo: { type: 'string', enum: ['none', 'established', 'contradicted'] },
          mark: S, why: S, evidence: SA,
        },
        required: ['id', 'status', 'pendingTo', 'mark', 'why', 'evidence'],
      },
    },
    top: SA,
    nullCase: { type: 'object', properties: { text: S, evidence: SA, none: S } },
    corrections: { type: 'array', items: { type: 'object', properties: { date: S, page: S, item: S, was: S, now: S, url: S }, required: ['date', 'item', 'was', 'now', 'url'] } },
    gaps: { type: 'array', items: { type: 'string' }, description: 'Reader-facing: what this edition could not assess and why, in plain sentences.' },
    notes: { type: 'array', items: { type: 'string' }, description: 'For the owner and later stages; never published.' },
  },
  required: ['headline', 'dek', 'claims', 'top', 'nullCase'],
}

const MOVE_CHECK = {
  type: 'object',
  properties: {
    id: S, holds: { type: 'boolean' }, status: { type: 'string', enum: STATUS },
    pendingHolds: { type: 'boolean' },
    why: { type: 'string', description: 'Your working notes for the run log. Never published.' },
    publishedWhy: { type: 'string', description: 'The published reason for the status you support: two to five sentences in the first person plural ("we"), quoting the claim\'s mark text in quotation marks for that status and for the next mark up that is not met, with the numbers that decide it. No "I", no stage names, no field names, no file paths.' },
  },
  required: ['id', 'holds', 'status', 'pendingHolds', 'why', 'publishedWhy'],
}

const RUN_OUTPUT = { type: 'object', properties: { exitCode: { type: 'number' }, output: S }, required: ['exitCode', 'output'] }

const REVIEW = {
  type: 'object',
  properties: {
    problems: { type: 'array', items: { type: 'object', properties: { where: S, problem: S, fix: S, severity: { type: 'string', enum: ['must', 'should'] } }, required: ['where', 'problem', 'fix', 'severity'] } },
    summary: S,
  },
  required: ['problems'],
}

const FIXED = { type: 'object', properties: { ok: { type: 'boolean' }, checkOutput: S, applied: SA, declined: SA }, required: ['ok', 'checkOutput'] }

// ---------------------------------------------------------------- lenses (spec 5.4)
const ALL_LENSES = [
  { key: 'capital', claims: ['J1', 'J8', 'J9'], title: 'Capital',
    brief: 'The core lens. How investors and capital allocators are already pricing AI\'s substitution for labor (J1: market reactions to AI-linked headcount news, AI and headcount language on earnings calls, venture share to AI, long-run real rates as the strong-form test); whether the AI capital bet runs ahead of its revenue and how it is financed (J8: AI capex against disclosed AI revenue, circular and vendor financing, data-center debt and private credit, depreciation lives, seat-revenue erosion against agent revenue at the pinned seat vendors); and whether the gains flow to owners rather than wages (J9: labor and profit shares, wealth and spending concentration, market concentration, top AI pay; and as evidence against, falling prices per unit of capability and open-weight parity).' },
  { key: 'work', claims: ['J2', 'J3', 'J6'], title: 'Work',
    brief: 'Firms and the labor market. J2: named AI-attributed hiring freezes and cuts WITH headcount evidence (statements alone never count), Challenger cuts citing AI, WARN notices, revenue per employee at the pinned firms, seat and retention disclosures at the pinned seat vendors with hyperscalers\' token volumes, quarterly headcount at the pinned Indian IT and BPO firms, JOLTS hires and quits by industry against the comparison industries (series/), freelance platforms\' filings and studies. J3: young workers in AI-exposed jobs against less-exposed peers, recent-graduate unemployment, junior postings, graduate intake, majors and exam volumes against pre-2022 trends. J6: new AI-era roles (expert data work, evaluation, AI operations) and their scale against the losses.' },
  { key: 'prices', claims: ['J5', 'J10'], title: 'Prices and moats',
    brief: 'J5, the human moats: trades pay against all private workers, apprenticeships, the physical-automation clock (humanoid robots: pilots versus paid production units and unit costs; industrial robot installations; robotaxi paid rides and cities), rules and rulings that keep or remove a licensed human\'s responsibility, care work. J10, Baumol: CPI for AI-exposed services against human-intensive services, employment shares of human-heavy sectors against information and professional services, consumption shares, all against pre-2022 trends (series/).' },
  { key: 'buyers', claims: ['J4', 'J11'], title: 'Bottlenecks and buyers',
    brief: 'J4, the physical bottlenecks: data-center power deals and nuclear restarts, capacity-market prices and large-load tariffs, interconnection queues, transformer and turbine lead times and backlogs, electricity prices against regions without data-center clusters, copper, bottleneck owners\' margins (big-tech capex itself belongs to the newsletter\'s money page; link, do not repeat). J11, the customer becomes an agent: agent payment rails and disclosed volumes, publishers\' search referral traffic and click-through with AI answers, search versus AI-answer advertising, AI-referred retail traffic, media and marketing cuts tied to AI search and agents.' },
  { key: 'policy', claims: ['J7', 'J12'], title: 'Policy and friction',
    brief: 'J7, policy separating income from work: guaranteed-income pilots and programs (especially any justified by automation), AI-dividend, sovereign-fund or public-equity proposals by legislative stage, automation or compute taxes, AI-justified transition payments. J12, backlash as a brake: union contracts with AI clauses and strikes over automation, local data-center denials and moratoriums and power-bill politics, laws restricting AI in hiring, firing and management and mandated human roles (federal pre-emption counts against J12), insurers\' AI exclusions and cyber surcharges and, as evidence against, affirmative AI cover, court rulings on liability for AI agents and AI decisions, polling on AI and jobs.' },
  { key: 'null', claims: ['J0'], title: 'The null',
    brief: 'J0, the null hypothesis: find ONLY the strongest evidence that, so far, this is a normal technology transition. Aggregate employment, wages and the pace of occupational change within past-wave ranges; studies finding no differential effect by AI exposure; productivity not breaking trend; and any evidence that undercuts J1-J12 specifically (a firm that cited AI and then rehired, a bottleneck easing, a moat holding for ordinary reasons). This lens keeps the tracker honest; it is never a summary of the others.' },
]
const LENSES = ONLY ? ALL_LENSES.filter(l => ONLY.indexOf(l.key) >= 0) : ALL_LENSES
if (!LENSES.length) throw new Error('jobs-weekly: args.only matched no lens; use capital, work, prices, buyers, policy or null')
const RAN = {}
LENSES.forEach(l => l.claims.forEach(c => { RAN[c] = true }))

// ---------------------------------------------------------------- 0. preflight
phase('Preflight')
const st = await runAgent([
  'Run exactly one command and return its output. Do nothing else: no edits, no other commands, no web.',
  'Command: cd ' + REPO + ' && python3 scripts/state.py --date ' + DATE,
  'It prints one JSON object. Return that object exactly as your structured output, field for field, without changing any value.',
].join('\n'), { label: 'state', phase: 'Preflight', schema: STATE })
if (!st || !Array.isArray(st.claims) || st.claims.length !== 13) throw new Error('jobs-weekly: could not read the run state (scripts/state.py)')
if (!BASELINE && !st.prev) throw new Error('jobs-weekly: no earlier edition exists; the first run must be the baseline (args.baseline = true)')
const CUR = {}
st.claims.forEach(c => { CUR[c.id] = c })
const PREV = {}
;((st.prev && st.prev.strip) || []).forEach(s => { PREV[s.id] = s.status })
const WINDOW = BASELINE
  ? 'the evidence base to date: everything that bears on the claim, with the most weight on the last 12 months; mark items older than 2026-01-01 as background'
  : 'from ' + dayAfter(st.prev.date) + ' (the day after the previous edition, ' + st.prev.date + ') through ' + DATE + '; older items only if the last edition missed them and they still matter, marked as background'
const STATE_NOTE = 'RUN STATE (from scripts/state.py): ' + JSON.stringify({ prev: st.prev ? st.prev.date : null, claims: st.claims, releases: st.releases, stale: st.stale })
log('Jobs ' + (BASELINE ? 'baseline' : 'edition') + ' ' + DATE + ': ' + LENSES.length + ' lens(es); ' + st.releases.length + ' series with new data; ' + st.stale.length + ' stale')

// ---------------------------------------------------------------- 1. research, verify, second refuter (no barrier)
function researchPrompt(l) {
  return [
    GROUND, '', EVIDENCE, '',
    'YOUR LENS: ' + l.title + ' (claims ' + l.claims.join(', ') + ').',
    l.brief,
    '',
    'First read claims.json for ' + l.claims.join(', ') + ': each claim\'s wording, marks and every indicator with its source, URL, confounders and comparison. ' + (st.prev ? 'Read the previous edition, ' + 'editions/' + st.prev.date + '.json, so you know what is already known. ' : '') + 'Read series/releases.json and the series/ files your indicators name for the official numbers.',
    'Window: ' + WINDOW + '.',
    STATE_NOTE,
    '',
    'Search broadly (primary sources first: statistical agencies, regulators, courts, filings and earnings materials, company statements, institutional research; then credible outlets), then open the sources. Return ' + (BASELINE ? '8-20' : '4-12') + ' items for this lens, each a single checkable statement with its event date, the best URL (primary where one exists), corroborating URLs, its kind and data kind, the rating you propose, which claims it bears on and in which direction (for or against; one item may bear on several claims), the confounder that applies, and "material" true when it could move a claim\'s status. Include the strongest evidence AGAINST your claims, not only for them. Ids: c1, c2, ... (ids are for this run only: an item\'s text never mentions another item\'s id).',
    'List sources you could not open (paywall, 403, browser challenge) in "blocked". Do not edit any repo file.',
  ].join('\n')
}

function verifyPrompt(l, found) {
  return [
    GROUND, '', EVIDENCE, '',
    'You are an ADVERSARIAL VERIFIER for the "' + l.title + '" lens. Another agent gathered the items below. Try to break every one of them. Assume each is wrong until its source proves it.',
    'For EVERY item: open the URL (and the corroborating ones); confirm the source states it, as its own claim, for that date or period; check numbers, names, quotes (speaker and date in the original) and the event date; for official numbers, check them against the series/ files; trace secondhand items to the original and give its URL (the intermediary goes in "via"); check the denylist; and assign the rating under the evidence rules. Return one result per item:',
    '- verified: supported as stated (the best primary URL in "url"; "correctedText" only if the wording needs tightening, as complete sentences);',
    '- downgraded: partly supported; the honest lower rating, and "correctedText" with the item rewritten so it is true as stated;',
    '- refuted: the source contradicts it or it misstates the source (rating "drop");',
    '- unverifiable: you could not confirm it from sources you opened (rating "drop"). No benefit of the doubt.',
    'Use "ratingQual" (5 words or fewer, e.g. "part our inference") only when a qualifier is needed, and "ratingNote" (one sentence) only to explain a rating. Put anything else you want later stages to know in "notes", never in "correctedText".',
    '',
    'ITEMS TO VERIFY (JSON):',
    JSON.stringify(found.items),
  ].join('\n')
}

function refutePrompt(l, items) {
  return [
    GROUND, '', EVIDENCE, '',
    'You are a SECOND, INDEPENDENT REFUTER for the "' + l.title + '" lens. These items survived one verifier and could move a claim\'s status. Look for what the first verifier missed: a later correction or retraction, a misread table, a wrong period, a number from press instead of the source, a confounder that fully explains it, a source that is not independent of another. Open the sources yourself. Default to refuted=true if you cannot confirm the item. When the item survives but needs fixing, give "correctedText": the item\'s complete text with the fix applied, as finished sentences (never instructions).',
    '',
    'ITEMS (JSON):',
    JSON.stringify(items),
  ].join('\n')
}

phase('Research')
const lensResults = await pipeline(
  LENSES,
  (_, l) => runAgent(researchPrompt(l), { label: 'research: ' + l.key, phase: 'Research', schema: FOUND }),
  (found, l) => {
    if (!found) return { lens: l, found: null, verdict: null }
    if (!(found.items || []).length) return { lens: l, found: found, verdict: { results: [] } }
    return runAgent(verifyPrompt(l, found), { label: 'verify: ' + l.key, phase: 'Research', schema: VERDICTS })
      .then(v => ({ lens: l, found: found, verdict: v }))
  },
  (r) => {
    if (!r || !r.verdict) return Object.assign({}, r, { refute: null })
    const byId = {}
    ;(r.verdict.results || []).forEach(x => { byId[x.id] = x })
    const material = (r.found.items || []).filter(c => c.material && byId[c.id] && byId[c.id].rating !== 'drop')
      .map(c => Object.assign({}, c, { text: byId[c.id].text || c.text, url: byId[c.id].url || c.url, rating: byId[c.id].rating }))
    if (!material.length) return Object.assign({}, r, { refute: { results: [] } })
    return runAgent(refutePrompt(r.lens, material), { label: 'refute: ' + r.lens.key, phase: 'Research', schema: REFUTE })
      .then(x => Object.assign({}, r, { refute: x || { results: [] }, refuterFailed: !x }))
  },
)

// ---------------------------------------------------------------- merge (plain code): final evidence ids e1..eN
// The text readers see: the refuter's corrected text, else the verifier's, else the researcher's. A "corrected" text that
// reads like an editing instruction (the 2026-10-06 rehearsal found ten) is refused in favour of the next one, and logged.
const INSTRUCTION = /^\s*(Rating:|Note:|Add |Replace |Optionally|Say |Change |Drop |Rewrite |Correct |Cite |Use the |Remove )/
const textNotes = []
function pickText(candidates, original, where) {
  for (const t of candidates) {
    if (!t || !String(t).trim()) continue
    if (INSTRUCTION.test(String(t))) { textNotes.push(where + ': a corrected text read like an instruction and was not used'); continue }
    return String(t).trim()
  }
  return original
}
const items = []
const dropped = []
const blocked = []
const gaps = []
for (const r of lensResults) {
  if (!r || !r.found) { gaps.push('lens ' + (r && r.lens ? r.lens.key : '?') + ': research failed'); continue }
  ;(r.found.blocked || []).forEach(b => blocked.push(r.lens.key + ': ' + b))
  if (!r.verdict) { gaps.push('lens ' + r.lens.key + ': verifier failed, its items are dropped'); continue }
  const byId = {}
  ;(r.verdict.results || []).forEach(x => { byId[x.id] = x })
  const ref = {}
  ;((r.refute && r.refute.results) || []).forEach(x => { ref[x.id] = x })
  for (const c of r.found.items || []) {
    const x = byId[c.id]
    if (!x || x.rating === 'drop' || x.verdict === 'refuted' || x.verdict === 'unverifiable') {
      dropped.push({ lens: r.lens.key, text: c.text, why: x ? x.verdict + ': ' + x.evidence : 'not checked by the verifier' })
      continue
    }
    if (c.material && r.refuterFailed) {
      dropped.push({ lens: r.lens.key, text: c.text, why: 'second refuter failed' })
      continue
    }
    if (ref[c.id] && ref[c.id].refuted) {
      dropped.push({ lens: r.lens.key, text: c.text, why: 'second refuter: ' + ref[c.id].evidence })
      continue
    }
    const fixedText = pickText([ref[c.id] && ref[c.id].correctedText, x.correctedText], c.text, r.lens.key + ':' + c.id)
    items.push({
      id: 'e' + (items.length + 1),
      text: fixedText,
      eventDate: x.eventDate || c.eventDate,
      background: !!c.background,
      url: x.url || c.url,
      otherUrls: c.otherUrls || [],
      via: x.via || null,
      rating: x.rating,
      ratingQual: x.ratingQual || null,
      ratingNote: x.ratingNote || null,
      kind: c.kind,
      dataKind: c.dataKind,
      bears: c.bears || [],
      confounder: c.confounder,
      top: false,
      lens: r.lens.key,
      material: !!c.material,
    })
  }
}
LENSES.length < ALL_LENSES.length && gaps.push('rehearsal: only the ' + LENSES.map(l => l.key).join(', ') + ' lens(es) ran')
st.stale.forEach(s => gaps.push('series ' + s + ' is stale (fetch failed); no move rests on it'))
log('Verified ' + items.length + ' items; dropped ' + dropped.length + '; ' + blocked.length + ' sources blocked')

// ---------------------------------------------------------------- 2. decide, then a refuter per proposed move
phase('Decide')
const decision = await runAgent([
  GROUND, '', EVIDENCE, '', MARKS, '',
  'You are the DECISION stage. Read claims.json in full (every claim\'s wording, marks, indicators and history)' + (st.prev ? ', the previous edition editions/' + st.prev.date + '.json' : '') + ', series/releases.json and the series/ files. Then decide, for EACH of the thirteen claims, its status for ' + DATE + ' under its own marks, using only the verified items below, the series and the claim\'s history.',
  STATE_NOTE,
  Object.keys(RAN).length < 13 ? 'REHEARSAL: no lens ran for ' + ['J0', 'J1', 'J2', 'J3', 'J4', 'J5', 'J6', 'J7', 'J8', 'J9', 'J10', 'J11', 'J12'].filter(c => !RAN[c]).join(', ') + '; give those claims their current status (No clear sign at a baseline) with the why "No lens ran for this claim in this rehearsal."' : '',
  '',
  'For each claim return: status (' + (BASELINE ? 'its starting status' : 'its current status, or one step from it') + '), pendingTo ("established" or "contradicted" when the evidence meets an extreme the owner must confirm, else "none"), mark (quote the mark text from claims.json you applied), why (three to five plain sentences in the "we" voice: quote, in quotation marks, the mark for the status you set and the mark for the next status up that is not met; then what the evidence shows, which indicators agree, and the confounders and why they do or do not explain it), and evidence (the item ids, e.g. ["e3", "e7"]; may be empty only for No clear sign).',
  'Also return: headline (at most 90 characters, plain, the week\'s most important finding, keeping the sources\' hedging; ' + (BASELINE ? 'for the baseline, where the claims start' : 'what moved or, in a quiet week, the most notable item') + '), dek (at most 60 words), top (the 3-8 item ids a reader should see first, the capital-positioning evidence among them), nullCase ({text, evidence} with the week\'s strongest evidence for J0 that it is a normal transition, or {none: reason} only if there truly is none), corrections (any earlier edition item that turned out wrong: {date, page: "jobs.html", item, was, now, url}), gaps (reader-facing: what you could not assess and why, in plain sentences) and notes (for the owner and later stages; never published).',
  '',
  'VERIFIED ITEMS (JSON):',
  JSON.stringify(items.map(i => ({ id: i.id, lens: i.lens, text: i.text, eventDate: i.eventDate, background: i.background, rating: i.rating, ratingQual: i.ratingQual, kind: i.kind, dataKind: i.dataKind, bears: i.bears, confounder: i.confounder, url: i.url }))),
].join('\n'), { label: 'decide', phase: 'Decide', schema: DECISION })
if (!decision) throw new Error('jobs-weekly: the decision stage failed')

const itemIds = {}
items.forEach(i => { itemIds[i.id] = true })
const D = {}
;(decision.claims || []).forEach(c => { D[c.id] = c })
const proposals = []
for (const c of st.claims) {
  const cur = BASELINE ? 'no-clear-sign' : c.status
  const d = D[c.id] || { status: cur, pendingTo: 'none', mark: '', why: 'No decision was returned for this claim.', evidence: [] }
  let status = STATUS.indexOf(d.status) >= 0 ? d.status : cur
  let pendingTo = d.pendingTo === 'established' || d.pendingTo === 'contradicted' ? d.pendingTo : null
  if (EXTREMES.indexOf(status) >= 0) {                       // a run never applies an extreme
    pendingTo = status
    status = BASELINE ? (status === 'established' ? 'supported' : 'no-clear-sign') : (cur === status ? cur : stepToward(cur, status))
    if (status === pendingTo) status = cur
  }
  if (!BASELINE && Math.abs(rank(status) - rank(cur)) > 1) {
    log(c.id + ': decision proposed ' + cur + ' -> ' + status + '; clamped to one step')
    status = stepToward(cur, status)
  }
  if (pendingTo && Math.abs(rank(pendingTo) - rank(status)) !== 1) pendingTo = null   // an extreme is pending only from its neighbour
  const evidence = (d.evidence || []).filter(e => itemIds[e])
  proposals.push({ id: c.id, label: c.label, current: BASELINE ? null : c.status, status: status, pendingTo: pendingTo, mark: d.mark || '', why: d.why || '', evidence: evidence })
}

function moveCheckPrompt(p) {
  const ev = items.filter(i => p.evidence.indexOf(i.id) >= 0)
  return [
    GROUND, '', EVIDENCE, '', MARKS, '',
    'You are a REFUTER of one proposed status. Read ' + p.id + ' in claims.json (wording, marks, indicators, history) and open the evidence below yourself. Try to break the proposal: is the mark it quotes actually met by these items (agreement of different kinds of indicator, sustained across releases, beyond the pre-2022 range or the comparison group, confounders examined)? Default to holds=false when in doubt.',
    'PROPOSAL: ' + JSON.stringify({ claim: p.id, from: BASELINE ? '(baseline)' : p.current, to: p.status, pendingTo: p.pendingTo, mark: p.mark, why: p.why }),
    'Return "why" (your working notes; never published) and "publishedWhy" (the reason readers see, in the "we" voice, quoting the mark text; it replaces the proposal\'s reason when holds is false).',
    BASELINE ? 'Return holds (does the evidence support this starting status?), status (the HIGHEST status on the scale the evidence does support, between No clear sign and the proposal, or Contradicted only if proposed and supported; never Established), pendingHolds (does the evidence meet the proposed pending extreme? false if none was proposed), why.' : 'Return holds (is the move to "' + p.status + '" supported?), status (the status the evidence supports: the proposal if it holds, else the current status ' + p.current + '), pendingHolds (does the evidence meet the proposed pending extreme? false if none was proposed), why.',
    '',
    'EVIDENCE (JSON):',
    JSON.stringify(ev),
  ].join('\n')
}

// A stage's working notes never reach a published reason (the 2026-10-06 baseline published three); they go to notes.
const WORKING = /\bI (opened|checked|downloaded|ran|read|found|confirmed|calculated)\b|The refuter found|pendingHolds|\.claude\/work/
const refuterNotes = []
const toCheck = proposals.filter(p => (BASELINE ? p.status !== 'no-clear-sign' : p.status !== p.current) || p.pendingTo)
log(toCheck.length + ' proposed status(es) go to a refuter')
const checks = await parallel(toCheck.map(p => () => runAgent(moveCheckPrompt(p), { label: 'refute move: ' + p.id, phase: 'Decide', schema: MOVE_CHECK })))
const CHECK = {}
checks.forEach((c, i) => { CHECK[toCheck[i].id] = c })
for (const p of proposals) {
  const c = CHECK[p.id]
  if (!(p.id in CHECK)) continue
  if (!c) {                                                    // refuter failed: nothing unrefuted is applied
    p.why += ' (The move refuter failed, so the proposal was not applied.)'
    p.status = BASELINE ? 'no-clear-sign' : p.current
    p.pendingTo = null
    continue
  }
  refuterNotes.push(p.id + ': ' + c.why)
  if (!c.holds) {
    let s = STATUS.indexOf(c.status) >= 0 ? c.status : (BASELINE ? 'no-clear-sign' : p.current)
    if (EXTREMES.indexOf(s) >= 0) s = BASELINE ? 'no-clear-sign' : p.current
    if (!BASELINE && s !== p.current && s !== p.status) s = p.current
    const pw = String(c.publishedWhy || '').trim()
    p.why = pw && !WORKING.test(pw) ? pw : 'The evidence did not support the proposed status under its mark, so we hold ' + s + '.'
    p.status = s
  }
  if (p.pendingTo && !c.pendingHolds) p.pendingTo = null
  if (p.pendingTo && Math.abs(rank(p.pendingTo) - rank(p.status)) !== 1) p.pendingTo = null
}

// ---------------------------------------------------------------- 3. write: the edition and the claims patch (plain code)
const topIds = (decision.top || []).filter(e => itemIds[e])
items.forEach(i => { i.top = topIds.indexOf(i.id) >= 0 })
const refs = ids => ids.map(e => DATE + '#' + e)
const moves = (st.ownerMoves || []).map(m => ({ id: m.id, from: m.from, to: m.to, why: m.why + ' (Confirmed by the owner on ' + m.date + '.)', evidence: [], by: 'owner' }))
const pendingOwner = []
const claimPatch = []
for (const p of proposals) {
  const cur = CUR[p.id]
  const patch = { id: p.id }
  if (BASELINE) {
    Object.assign(patch, { status: p.status, since: DATE, history: { date: DATE, from: null, to: p.status, why: p.why, evidence: refs(p.evidence), by: 'run' } })
  } else if (p.status !== p.current) {
    moves.push({ id: p.id, from: p.current, to: p.status, why: p.why, evidence: p.evidence, by: 'run' })
    Object.assign(patch, { status: p.status, since: DATE, history: { date: DATE, from: p.current, to: p.status, why: p.why, evidence: refs(p.evidence), by: 'run' } })
  }
  if (p.pendingTo) {
    patch.pending = { to: p.pendingTo, since: DATE, why: p.why, evidence: refs(p.evidence) }
    pendingOwner.push({ id: p.id, from: p.status, to: p.pendingTo, why: p.why, evidence: p.evidence })
  } else if (cur.pending && (BASELINE || p.status !== p.current || Math.abs(rank(cur.pending.to) - rank(p.status)) !== 1)) {
    patch.pending = null                                       // a carried pending lapses when the claim moved away from it
  } else if (cur.pending) {
    pendingOwner.push({ id: p.id, from: p.status, to: cur.pending.to, why: cur.pending.why + ' (Awaiting the owner since ' + cur.pending.since + '.)', evidence: [] })
  }
  if (Object.keys(patch).length > 1) claimPatch.push(patch)
}
const pendingOf = {}
pendingOwner.forEach(x => { pendingOf[x.id] = x.to })
const decided = {}
;(decision.claims || []).forEach(c => { decided[c.id] = c.status + '|' + (c.pendingTo || 'none') })
const changed = proposals.filter(p => decided[p.id] !== p.status + '|' + (p.pendingTo || 'none'))
let headline = decision.headline
let dek = decision.dek
if (changed.length) {
  log('The refuters changed ' + changed.map(p => p.id).join(', ') + ': rewriting the headline and dek to match')
  const copy = await runAgent([
    GROUND, '', EVIDENCE, '',
    'Write the headline and dek for the Jobs ' + (BASELINE ? 'baseline' : 'edition') + ' of ' + DATE + ' so they match the FINAL statuses below (the refuters changed some after the first draft). Headline: at most 90 characters, plain, keeping the sources\' hedging. Dek: at most 60 words. Name a status only as it stands in the list; a pending extreme is "proposed for the owner", never reached. No web, no files, no tools.',
    'FINAL STATUSES (JSON): ' + JSON.stringify(proposals.map(p => ({ id: p.id, label: p.label, status: p.status, pendingTo: p.pendingTo, why: p.why }))),
    'FIRST DRAFT, to correct: ' + JSON.stringify({ headline: decision.headline, dek: decision.dek }),
  ].join('\n'), { label: 'headline', phase: 'Decide', schema: { type: 'object', properties: { headline: S, dek: S }, required: ['headline', 'dek'] } })
  if (copy && copy.headline) { headline = copy.headline; dek = copy.dek || dek }
}
const readerGaps = gaps.slice()
if (blocked.length) readerGaps.push(blocked.length + ' sources could not be opened (paywalls, or sites that block automated access); items rest on other copies or sources, and the list is in the run log.')
if (BASELINE) readerGaps.push('In this baseline, items dated before 2026 are marked as background.')
const nc = decision.nullCase || {}
const nullCase = nc.none && !nc.text ? { none: nc.none } : { text: nc.text || 'No evidence for the null this week.', evidence: (nc.evidence || []).filter(e => itemIds[e]) }
const edition = {
  schema: 1,
  date: DATE,
  claimsVersion: st.claimsVersion,
  baseline: BASELINE,
  window: { from: BASELINE ? null : dayAfter(st.prev.date), to: DATE },
  headline: headline,
  dek: dek,
  strip: proposals.map(p => ({ id: p.id, status: p.status, prev: BASELINE ? null : (PREV[p.id] || null), pending: pendingOf[p.id] ? { to: pendingOf[p.id] } : null })),
  moves: moves,
  pendingOwner: pendingOwner,
  evidence: items.map(i => ({ id: i.id, text: i.text, eventDate: i.eventDate, background: i.background, url: i.url, otherUrls: i.otherUrls, via: i.via, rating: i.rating, ratingQual: i.ratingQual, ratingNote: i.ratingNote, kind: i.kind, dataKind: i.dataKind, bears: i.bears, confounder: i.confounder, top: i.top })),
  nullCase: nullCase,
  releases: st.releases,
  gaps: readerGaps.concat(decision.gaps || []),
  corrections: decision.corrections || [],
}
const payload = { edition: edition, claims: claimPatch }

phase('Write')
const written = await runAgent([
  'You write two files and run one command. Do nothing else: no web, no other edits, no git.',
  '1. mkdir -p ' + WORK,
  '2. Write the JSON below to ' + WORK + '/payload.json EXACTLY as given: byte for byte, no reformatting, no edits, no added or removed fields.',
  '3. Run: cd ' + REPO + ' && python3 scripts/apply_edition.py ' + WORK + '/payload.json',
  'Return its exit code and its full output.',
  '',
  'PAYLOAD (JSON):',
  JSON.stringify(payload),
].join('\n'), { label: 'write', phase: 'Write', schema: RUN_OUTPUT })
if (!written) throw new Error('jobs-weekly: the write stage failed')
log('apply_edition.py exit ' + written.exitCode)

// ---------------------------------------------------------------- 4. review and fix
phase('Review')
const review = await runAgent([
  GROUND, '', EVIDENCE, '', MARKS, '',
  'You are a HOSTILE REVIEWER of the Jobs ' + (BASELINE ? 'baseline' : 'edition') + ' just written to ' + EDITION + ' (and the claims.json changes it made: compare with `git diff claims.json`). Find everything wrong. Check:',
  '- every item cited by a move, a pending proposal, the null case or marked top: open its URL and confirm the text, date and rating; spot-check the rest;',
  '- ratings and attribution ("via") under the rules; event dates; that each item names a real confounder;',
  '- that each status follows the claim\'s own marks in claims.json, the one-step rule' + (BASELINE ? ' (not at the baseline), no claim starting at an extreme' : '') + ', and that no move rests on a stale series;',
  '- that the null case is present and genuinely the strongest evidence for J0;',
  '- overclaiming ("proof", "proves", "shows that" for our inference), investment language, dramatic words, the headline (at most 90 characters) and dek (at most 60 words);',
  '- that claims.json changed only status, since, pending and appended history rows (never wording, marks, indicators or lists).',
  'apply_edition.py said (exit ' + written.exitCode + '):',
  written.output,
  'Return each problem with where (a field path such as "evidence e4.rating" or "strip J3"), the problem, the exact fix, and severity: "must" (wrong, unsourced, against the rules or failing the check) or "should" (clearer or better).',
].join('\n'), { label: 'review', phase: 'Review', schema: REVIEW })

const problems = (review && review.problems) || []
let fixed = null
if (problems.length || written.exitCode !== 0) {
  fixed = await runAgent([
    GROUND, '', EVIDENCE, '', MARKS, '',
    'You are the FIXER for ' + EDITION + '. Apply every "must" fix below and every "should" fix that is clearly right, by editing ' + EDITION + ' and, only where a status changes, claims.json (only status, since, pending, and the history row dated ' + DATE + ' that this run appended; never wording, marks, indicators, lists or older history rows). Keep the edition and claims.json consistent: the strip, the moves, pendingOwner, the history row and the claim\'s status must agree; an evidence id you drop must also leave every move, pending and null case that cites it. Then run: cd ' + REPO + ' && python3 scripts/check_plugin.py and repeat until it prints CHECK OK.',
    'Do not add new evidence items. If a status can no longer be supported after a fix, step it back (to the current status' + (BASELINE ? ', or No clear sign at the baseline' : '') + ') and say so in the why.',
    '',
    'REVIEW (JSON):',
    JSON.stringify(review || { problems: [] }),
    'apply_edition.py said (exit ' + written.exitCode + '):',
    written.output,
    'Return ok (true when the check prints CHECK OK), the check output, the fixes applied and the ones declined with why.',
  ].join('\n'), { label: 'fix', phase: 'Review', schema: FIXED })
}

// Ready only when the write passed and the review either found nothing or its fixes were applied and re-checked: an
// unreviewed or unfixed edition is never ready (the 2026-10-06 baseline's fixer was blocked and the run said ready).
const ready = written.exitCode === 0 && !!review && (problems.length === 0 || (!!fixed && !!fixed.ok))
return {
  ready: ready,
  date: DATE,
  baseline: BASELINE,
  headline: edition.headline,
  strip: edition.strip.map(s => s.id + ' ' + s.status + (s.pending ? ' (pending ' + s.pending.to + ')' : '')),
  moves: moves.map(m => m.id + ' ' + m.from + ' -> ' + m.to + ' (' + m.by + ')'),
  pendingOwner: pendingOwner.map(x => x.id + ' -> ' + x.to),
  items: items.length,
  dropped: dropped.length,
  gaps: edition.gaps,
  notes: (decision.notes || []).concat(textNotes).concat(refuterNotes),
  blocked: blocked,
  fallbacks: fallbacks,
  review: { problems: problems.length, must: problems.filter(p => p.severity === 'must').length, summary: review ? review.summary : 'review failed' },
  fix: fixed ? { ok: fixed.ok, applied: (fixed.applied || []).length, declined: fixed.declined || [] } : null,
  check: fixed ? fixed.checkOutput : written.output,
}
