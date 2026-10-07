// Runs .claude/workflows/jobs-weekly.js under Node with stubbed agent/pipeline/parallel and scripted agent replies.
// From the final whole-branch review of 2026-10-06; used by test_workflow.py (skipped when node is missing).
import fs from 'fs'
const SRC = fs.readFileSync(new URL('../../.claude/workflows/jobs-weekly.js', import.meta.url), 'utf8').replace('export const meta =', 'const meta =')
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const IDS = Array.from({ length: 13 }, (_, i) => 'J' + i)
const LENS = { capital: ['J1', 'J8', 'J9'], work: ['J2', 'J3', 'J6'], prices: ['J5', 'J10'], buyers: ['J4', 'J11'], policy: ['J7', 'J12'], null: ['J0'] }

export async function run(args, responders) {
  const logs = []
  let payload = null
  const agent = async (prompt, o) => {
    const label = o.label
    if (label === 'write') payload = JSON.parse(prompt.split('PAYLOAD (JSON):\n')[1])
    const r = responders(label, prompt, o)
    if (r instanceof Error) throw r
    return r === undefined ? null : JSON.parse(JSON.stringify(r))
  }
  const pipeline = async (items, ...stages) => Promise.all(items.map(async (it, i) => {
    let prev = it
    for (let s = 0; s < stages.length; s++) {
      try { prev = await stages[s](s === 0 ? it : prev, it, i) } catch (e) { logs.push('pipeline stage threw: ' + e.message); return null }
    }
    return prev
  }))
  const parallel = async thunks => Promise.all(thunks.map(async t => { try { return await t() } catch (e) { return null } }))
  const f = new AsyncFunction('args', 'agent', 'pipeline', 'parallel', 'phase', 'log', SRC)
  const out = await f(args, agent, pipeline, parallel, () => {}, m => logs.push(m))
  return { out, payload, logs }
}

export function baseState(over) {
  return Object.assign({
    date: '2026-10-15', claimsVersion: '1.0', prev: { date: '2026-10-06', strip: IDS.map(id => ({ id, status: 'no-clear-sign', prev: null, pending: null })) },
    claims: IDS.map(id => ({ id, label: id, status: 'no-clear-sign', pending: null })), ownerMoves: [], releases: [], stale: [],
  }, over || {})
}

export function stdResponders(st, opts) {
  opts = opts || {}
  return (label, prompt) => {
    if (label === 'state') return st
    if (label.startsWith('research: ')) {
      const k = label.slice(10)
      if (opts.researchFail && opts.researchFail[k]) return opts.researchFail[k]
      return { lens: k, items: LENS[k].map((c, i) => ({ id: 'c' + (i + 1), text: 'Item for ' + c + '.', eventDate: '2026-10-10', url: 'https://example.org/' + c, kind: 'press', dataKind: 'private', proposedRating: 'credible report', bears: [{ claim: c, direction: 'for' }], confounder: 'x', material: false })) }
    }
    if (label.startsWith('verify: ')) {
      const k = label.slice(8)
      if (opts.verifyFail && opts.verifyFail[k]) return opts.verifyFail[k]
      return { results: LENS[k].map((c, i) => ({ id: 'c' + (i + 1), verdict: 'verified', rating: 'credible report', evidence: 'ok' })) }
    }
    if (label.startsWith('refute: ')) return { results: [] }
    if (label === 'decide') return opts.decision
    if (label.startsWith('refute move: ')) {
      const id = label.slice(13)
      if (opts.moveCheck && id in opts.moveCheck) return opts.moveCheck[id]
      return { id, holds: true, status: 'no-clear-sign', pendingHolds: true, why: 'ok', publishedWhy: '' }
    }
    if (label === 'headline') return opts.headline
    if (label === 'write') return opts.write || { exitCode: 0, output: 'CHECK OK' }
    if (label === 'review') return 'review' in opts ? opts.review : { problems: [] }
    if (label === 'fix') return 'fix' in opts ? opts.fix : { ok: true, checkOutput: 'CHECK OK' }
    return null
  }
}
export function decision(statuses, over) {
  return Object.assign({ headline: 'H', dek: 'D', claims: IDS.map(id => Object.assign({ id, status: 'no-clear-sign', pendingTo: 'none', mark: 'm', why: 'w', evidence: [] }, (statuses || {})[id] || {})), top: [], nullCase: { text: 't', evidence: [] } }, over || {})
}
