/**
 * Microbench scaffold (TypeScript / tinybench) with the discipline from
 * references/verification.md → Microbench discipline.
 *
 * What this scaffold gets right (so you don't have to remember every time):
 *   - Defeats dead-code elimination by accumulating a side-effecting result.
 *   - Sweeps the access pattern: sequential, random, zipfian.
 *   - Sweeps the working-set size to expose cache effects.
 *   - Reports median + variance (tinybench does this).
 *   - Warmup phase to wait out V8 PGO / inlining transitions.
 *
 * To adapt:
 *   1. Replace `MyStructure` with your real impl.
 *   2. Adjust `WORKLOAD_SIZES` and `DISTRIBUTIONS` to match what you care about.
 *   3. Add benches for the specific operations on your hot path.
 *
 * Install:
 *   npm install --save-dev tinybench
 *
 * Run:
 *   npx tsx scripts/bench.ts
 *
 * Hostile environments:
 *   - Disable HW prefetch / CPU boost where you can.
 *   - On Linux: `taskset -c 0 nice -n -20 npx tsx scripts/bench.ts`.
 *   - On macOS (M-series): noise is unavoidable from short runs — use
 *     longer durations (set `time: 2000` or higher).
 */

import { Bench } from "tinybench";

// ---------------------------------------------------------------------------
// 1. Replace with your real structure.
// ---------------------------------------------------------------------------

class MyStructure {
  private items = new Map<number, number>();

  insert(k: number, v: number): void {
    this.items.set(k, v);
  }

  lookup(k: number): number | undefined {
    return this.items.get(k);
  }

  delete(k: number): void {
    this.items.delete(k);
  }
}

// ---------------------------------------------------------------------------
// 2. Workload generators. Same shape for every bench — change the
//    distribution to expose how the structure responds to different access
//    patterns.
// ---------------------------------------------------------------------------

const WORKLOAD_SIZES = [1_000, 10_000, 100_000];
type Distribution = "sequential" | "random" | "zipfian";
const DISTRIBUTIONS: Distribution[] = ["sequential", "random", "zipfian"];

// Mulberry32 — small, deterministic PRNG (so benches are reproducible).
function mulberry32(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function genKeys(n: number, distribution: Distribution, seed = 0xC0FFEE): Int32Array {
  const out = new Int32Array(n);
  const rand = mulberry32(seed);
  switch (distribution) {
    case "sequential": {
      for (let i = 0; i < n; i++) out[i] = i;
      return out;
    }
    case "random": {
      for (let i = 0; i < n; i++) out[i] = (rand() * n * 10) | 0;
      return out;
    }
    case "zipfian": {
      // Approximate Zipf via inverse-CDF; alpha ≈ 1.5.
      const alpha = 1.5;
      const denom = Math.pow(n, 1 - alpha) - 1;
      for (let i = 0; i < n; i++) {
        const u = rand();
        const val = Math.pow(u * denom + 1, 1 / (1 - alpha));
        out[i] = (val | 0) % (n * 10);
      }
      return out;
    }
  }
}

function populate(s: MyStructure, keys: Int32Array): void {
  for (let i = 0; i < keys.length; i++) {
    s.insert(keys[i]!, i);
  }
}

// ---------------------------------------------------------------------------
// 3. Black-hole sink. V8 can prove an unused result is dead and erase the
//    work. Accumulate into a module-level var and print it at the end.
// ---------------------------------------------------------------------------

let sink = 0;

function consume(x: unknown): void {
  if (x === undefined || x === null) sink ^= 1;
  else if (typeof x === "number") sink ^= x | 0;
  else if (typeof x === "string") sink ^= x.length;
  else sink ^= 1;
}

// ---------------------------------------------------------------------------
// 4. Build a parametrized bench across (size, distribution).
// ---------------------------------------------------------------------------

async function main(): Promise<void> {
  console.log("# tinybench scaffold");

  for (const n of WORKLOAD_SIZES) {
    for (const dist of DISTRIBUTIONS) {
      const bench = new Bench({
        // Warmup defends against V8 PGO not having converged.
        warmupIterations: 100,
        warmupTime: 100,
        time: 1000, // measure each bench for ~1s
      });

      const insertKeys = genKeys(n, dist, 0xFACE);

      bench.add(`insert N=${n} dist=${dist}`, () => {
        const s = new MyStructure();
        for (let i = 0; i < insertKeys.length; i++) {
          s.insert(insertKeys[i]!, i);
        }
        consume(insertKeys.length);
      });

      // Lookup bench: pre-populated structure, random query keys (separate seed).
      const populated = new MyStructure();
      populate(populated, insertKeys);
      const queryKeys = genKeys(n, "random", 0xBEEF);

      bench.add(`lookup N=${n} dist=${dist}`, () => {
        for (let i = 0; i < queryKeys.length; i++) {
          consume(populated.lookup(queryKeys[i]!));
        }
      });

      // Mixed workload: 80% lookup, 15% insert, 5% delete.
      const mixedKeys = genKeys(n, "random", 0xDEAD);
      const rand = mulberry32(0xBEEF);
      const rolls = new Float32Array(n);
      for (let i = 0; i < n; i++) rolls[i] = rand();

      bench.add(`mixed (80r/15w/5d) N=${n} dist=${dist}`, () => {
        const s = new MyStructure();
        populate(s, insertKeys);
        for (let i = 0; i < mixedKeys.length; i++) {
          const k = mixedKeys[i]!;
          const r = rolls[i]!;
          if (r < 0.8) consume(s.lookup(k));
          else if (r < 0.95) s.insert(k, 1);
          else s.delete(k);
        }
      });

      await bench.run();

      console.log(`\n## N=${n} dist=${dist}`);
      console.table(
        bench.tasks.map(({ name, result }) => ({
          name,
          "hz (ops/s)": result?.hz.toFixed(2) ?? "—",
          "mean (ns)": result ? (result.mean * 1e6).toFixed(2) : "—",
          "p99 (ns)": result?.p99 ? (result.p99 * 1e6).toFixed(2) : "—",
          rme: result?.rme?.toFixed(2) ?? "—",
          samples: result?.samples?.length ?? 0,
        })),
      );
    }
  }

  // Print env for the report. ALWAYS report alongside numbers (see
  // references/verification.md → Bench reporting template).
  console.log("\n# Bench environment");
  console.log(`# Node: ${process.version}`);
  console.log(`# Platform: ${process.platform} ${process.arch}`);
  console.log(`# Sink (defeats DCE): 0x${sink.toString(16)}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
