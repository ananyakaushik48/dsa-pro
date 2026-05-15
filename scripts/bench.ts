// Microbench scaffold (TypeScript + tinybench).
//
// Install: npm i -D tinybench
// Run:     npx tsx bench.ts
//
// Disciplines applied:
//   - Distribution sweep: sequential / random / zipfian
//   - Working-set sweep: tiny / fits-L1 / fits-L2 / spills to DRAM
//   - Sink to defeat DCE
//   - Report median + (max - min) / median (relative range)

import { Bench } from 'tinybench'

// Anti-DCE sink. Without something like this, the JIT can elide the loop body.
let SINK = 0
const consume = (x: number) => { SINK ^= x | 0 }

// Pareto-ish heavy-tail (zipfian-ish): few keys hit very often.
function zipfianKeys(n: number, alpha = 1.1): number[] {
  const ranks = new Array(n).fill(0).map((_, i) => 1 / Math.pow(i + 1, alpha))
  const total = ranks.reduce((a, b) => a + b, 0)
  const cdf: number[] = []
  let acc = 0
  for (const r of ranks) { acc += r / total; cdf.push(acc) }
  const out = new Array(n)
  for (let i = 0; i < n; i++) {
    const u = Math.random()
    let lo = 0, hi = cdf.length
    while (lo < hi) { const m = (lo + hi) >> 1; if (cdf[m] < u) lo = m + 1; else hi = m }
    out[i] = lo
  }
  return out
}

function randomKeys(n: number): number[] {
  const a = new Array(n)
  for (let i = 0; i < n; i++) a[i] = (Math.random() * 0x7fffffff) | 0
  return a
}

function seqKeys(n: number): number[] {
  const a = new Array(n)
  for (let i = 0; i < n; i++) a[i] = i
  return a
}

const distributions = {
  sequential: seqKeys,
  random: randomKeys,
  zipfian: (n: number) => zipfianKeys(n, 1.1),
}

const workingSets = [
  { name: '4 K (L1-ish)', n: 4_000 },
  { name: '64 K (L2-ish)', n: 64_000 },
  { name: '1 M (DRAM)', n: 1_000_000 },
]

// ─── Replace with the candidate(s) you want to compare. ───
function buildCandidateMap(): Map<number, number> { return new Map() }
function buildOracleObject(): Record<number, number> { return Object.create(null) }

async function runOnce(label: string, n: number, keys: number[]) {
  const bench = new Bench({ time: 2_000, warmupTime: 500, warmupIterations: 32 })

  bench.add(`${label}  Map.set`, () => {
    const m = buildCandidateMap()
    for (let i = 0; i < n; i++) m.set(keys[i], i)
    consume(m.size)
  })

  bench.add(`${label}  Object[] write`, () => {
    const o = buildOracleObject()
    for (let i = 0; i < n; i++) o[keys[i]] = i
    consume(Object.keys(o).length)
  })

  bench.add(`${label}  Map.get`, () => {
    const m = buildCandidateMap()
    for (let i = 0; i < n; i++) m.set(keys[i], i)
    let acc = 0
    for (let i = 0; i < n; i++) acc += m.get(keys[i]) ?? 0
    consume(acc)
  })

  await bench.warmup()
  await bench.run()
  console.table(
    bench.tasks.map((t) => ({
      name: t.name,
      'p50 (ns)': t.result!.mean ? (t.result!.mean * 1_000_000).toFixed(1) : '-',
      'rel. range': t.result!.mean
        ? (((t.result!.max - t.result!.min) / t.result!.mean) * 100).toFixed(1) + '%'
        : '-',
      'samples': t.result!.samples.length,
    })),
  )
}

;(async () => {
  for (const [distName, distFn] of Object.entries(distributions)) {
    for (const ws of workingSets) {
      const keys = distFn(ws.n)
      console.log(`\n--- ${distName} keys, ${ws.name} ---`)
      await runOnce(`${distName}/${ws.name}`, ws.n, keys)
    }
  }
  // Force-print sink so the optimizer can't elide it.
  console.log('sink:', SINK)
})()
