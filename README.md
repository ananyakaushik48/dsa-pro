# dsa-pro

[![skills.sh](https://skills.sh/b/ananyakaushik48/dsa-pro)](https://skills.sh/ananyakaushik48/dsa-pro)

A senior-engineer **agent skill** that takes a software project from fuzzy intent to production-grade code — and keeps it production-grade as it evolves.

Combines a full project-planning + SDLC playbook with a deep data-structure and algorithm catalogue. Built for the persona of a veteran engineer who treats Big-O reasoning as the floor, the memory hierarchy and stdlib idioms as the ceiling, and property tests + microbenchmarks as the proof.

> Compatible with the [skills.sh](https://skills.sh) open agent skills ecosystem — works in Claude Code, Codex, Cursor, OpenCode, and 50+ other agents.

## Install

### Via the skills CLI (recommended)

```bash
# Install into the current project
npx skills add ananyakaushik48/dsa-pro

# Or install globally for all projects
npx skills add ananyakaushik48/dsa-pro -g

# Target a specific agent (e.g. Claude Code only)
npx skills add ananyakaushik48/dsa-pro -a claude-code
```

The CLI auto-detects which agents you have installed and symlinks the skill into each one's skills directory. See the [skills CLI docs](https://github.com/vercel-labs/skills) for `--agent`, `--global`, `--copy`, and other flags.

### Manual install (Claude Code)

```bash
git clone https://github.com/ananyakaushik48/dsa-pro.git ~/Projects/dsa-pro
mkdir -p ~/.claude/skills
ln -s ~/Projects/dsa-pro ~/.claude/skills/dsa-pro
```

Claude Code picks the skill up automatically the next time it scans skills.

## What's inside

```
dsa-pro/
├── SKILL.md                          # Trigger conditions, principles, workflow, file map
├── references/
│   ├── sdlc.md                       # 6 SDLC traditions (Agile, Lean, DevOps, TDD, Waterfall, DDD)
│   ├── project-planning.md           # Discovery → decomposition → roadmap walkthrough
│   ├── principles.md                 # SOLID, DRY, YAGNI, KISS, parse-don't-validate, quality attributes
│   ├── templates.md                  # PRD, ADR, WBS, story, DoD, postmortem, traceability matrix, …
│   ├── decision-tree.md              # want → reach for → fall back → trap (the structure picker)
│   ├── catalogue.md                  # Every DS family: invariants, Big-O, language idioms, traps
│   ├── algorithms.md                 # Sort / search / graph / string / DP / number / geometry / bit / stream
│   └── verification.md               # Invariant checks, oracle pattern, property tests, microbench discipline
└── scripts/
    ├── scaffold_project.py           # Generate a planning directory (PRD, ADRs, WBS, risk register) from CLI args
    ├── proptest.{py,ts,rs}           # Property-test scaffolds (hypothesis / fast-check / proptest)
    └── bench.{py,ts,rs}              # Microbench scaffolds (pytest-benchmark / tinybench / criterion)
```

## When the skill triggers

**Planning / architecture / process.** "Help me plan a project," "what SDLC fits this?", "write me a PRD / ADR / spec," "how do I split this into modules / bounded contexts?", "review my architecture."

**Data-structure / algorithm choice.** Anything that stores, indexes, searches, sorts, traverses, batches, ranks, joins, deduplicates, or streams data — when the answer isn't a one-liner. Choosing between `Map`, `Set`, `PriorityQueue`. Picking in-memory vs on-disk indexes. "Make it faster."

If the task is `arr.push(x)` or `Object.keys(o)`, the skill is overkill.

See [`SKILL.md`](SKILL.md) for the full trigger list and workflow.

## Why this exists

Most "data structures" references stop at "here's a BST, here's a hash table." This skill goes further:

- **Translates user intent into a structure + algorithm pairing.** Decision tables map operations and access patterns to canonical picks, with a fallback and a named trap for each.
- **Treats the stdlib as the default.** `HashMap`, `BTreeMap`, `priority_queue` — beating them is a project, not a function. Custom containers are reserved for what the stdlib provides poorly: cache layout, on-disk format, concurrency model, persistence.
- **Language-portable.** Pseudocode + idiom notes for C / C++ / Rust / Go / Java / Python / TypeScript. Calls out gotchas (Python `heapq` is min-only; Rust `BinaryHeap` is max; Java `PriorityQueue` is min by natural order; etc.).
- **Hardware-aware.** L1/L2/L3/DRAM/NVMe/network latency ratios drive structure choice as much as Big-O. SoA vs. AoS, cache lines, branch prediction, allocator behavior — all live alongside the code.
- **SDLC-honest.** A regulated medical device plan is not a Lean MVP plan. The skill matches process to risk and doesn't pretend Agile fits every project.
- **Verifiable.** Property-test scaffolds use the oracle pattern (test candidate against a trivially-correct reference) plus invariant checks after every op. Microbench scaffolds sweep working-set sizes and key distributions, defeat DCE, and report median + dispersion.

## Scope

**Project planning & SDLC**

- Discovery briefs, PRDs, ADRs, work breakdown, roadmaps, risk registers, traceability matrices, postmortems, module specs.
- Agile, Lean / MVP, DevOps / CI-CD, TDD / property-test-first, Waterfall (regulated medical & finance), DDD / hexagonal — with anti-patterns and when-not-to-use.
- Verification plans tied to SDLC cadence.

**Data structures**

- **Contiguous**: dynamic array, ring buffer, deque, packed bitset, slot map, columnar / SoA.
- **Linked**: singly / doubly / skip list / intrusive.
- **Search trees**: BST, AVL, red-black, treap, splay, scapegoat, in-memory B-tree.
- **Range trees**: Fenwick (BIT), segment tree (lazy), persistent segment tree, sparse table, wavelet tree.
- **Disk / write-heavy**: B-tree, B+ tree, LSM, fractal tree, copy-on-write B-tree.
- **Heaps**: binary, d-ary, pairing, Fibonacci, indexed, min-max.
- **Hashing**: open addressing (linear / Robin Hood / hopscotch / cuckoo), separate chaining; SipHash / xxHash / wyhash; concurrent variants.
- **Graphs**: adjacency list / matrix / CSR / edge list.
- **Tries**: standard, radix / Patricia, HAMT, suffix tree, suffix automaton.
- **Probabilistic**: Bloom, Counting Bloom, Cuckoo filter, Count-Min, HyperLogLog, t-digest, MinHash.
- **Union-Find**: union by rank + path compression.
- **Persistent**: HAMT, persistent vector, RRB-tree, finger tree, path-copy persistent trees.
- **Concurrent / lock-free**: Treiber stack, Michael-Scott queue, Vyukov MPSC, LMAX Disruptor, RCU, hazard pointers, epoch-based reclamation, sharded / lock-striped maps.
- **Spatial**: KD-tree, R-tree / R*-tree, quadtree / octree, BVH, Z-order / Hilbert.
- **Text-edit**: rope, gap buffer, piece table, CRDT pointers.

**Algorithms**

- **Sort**: introsort, pdqsort, Timsort, heapsort, mergesort, counting / radix / bucket, external merge, parallel.
- **Selection**: quickselect, median of medians, top-K via heap, order-statistic tree.
- **Search**: binary / lower / upper bound, exponential, ternary, fractional cascading.
- **Graph**: BFS / DFS, Dijkstra, Bellman-Ford, SPFA, Floyd-Warshall, Johnson's, A*, Yen's, Kruskal, Prim, Tarjan SCC, Kosaraju, Kahn's, bridges / articulation, 2-SAT, Edmonds-Karp, Dinic's, push-relabel, min-cost max-flow, Hopcroft-Karp, Hungarian, Edmonds' blossom.
- **Strings**: KMP, Z, Rabin-Karp, Aho-Corasick, Manacher, suffix array + LCP, suffix automaton, BWT / FM-index.
- **Dynamic programming**: knapsack family, LIS / LCS / edit distance, matrix-chain, bitmask, tree, digit, profile; Knuth, CHT / Li Chao, divide-and-conquer DP, SOS, Aliens trick.
- **Number theory**: GCD / extended GCD, modpow, modular inverse, sieve (Eratosthenes / linear), Miller-Rabin, Pollard's rho, CRT, totient.
- **Geometry**: cross / CCW, convex hull (monotone chain / Graham), point-in-polygon, segment intersection (Bentley-Ottmann), closest pair, rotating calipers, half-plane intersection, KD nearest-neighbor.
- **Bit tricks**: popcount, ctz / clz, lowbit, subset iteration, XOR identities, Gosper's hack.
- **Streaming / online**: reservoir sampling (Algorithm R / L), sliding window min / max, Misra-Gries, Welford, online median.
- **Randomization**: Fisher-Yates, Vose's alias method, Las Vegas vs Monte Carlo.

## Contributing

Pull requests welcome. Conventions:

- Pseudocode is the canonical form; language-specific notes call out the stdlib name + gotcha.
- Every structure entry must include invariants, complexity, when-to-use, when-not, language idiom notes, production traps.
- New algorithms come with a recognizable problem shape (the "this looks like" entry in [`references/algorithms.md`](references/algorithms.md)).
- Scaffolds in `scripts/` must use the oracle pattern (proptest) or working-set / distribution sweeps (bench).

## License

MIT — see [`LICENSE`](LICENSE).
