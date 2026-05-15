# dsa-pro

A senior-engineer-grade Claude Code skill for picking and implementing the right **data structures + algorithms** for any problem, across any language or hardware target.

> Built for the persona of a veteran software engineer who treats Big-O reasoning as the floor, the memory hierarchy and stdlib idioms as the ceiling, and property tests + microbenchmarks as the proof.

## What's inside

```
dsa-pro/
├── SKILL.md                       # Trigger conditions, mental model, workflow
├── references/
│   ├── catalogue.md               # Every structure family: invariants, Big-O, language idioms, traps
│   ├── algorithms.md              # Sort / search / graph / string / DP / number / geometry / bit / streaming
│   ├── decision-tree.md           # "I need X" → reach for Y, fall back to Z, watch out for trap T
│   └── verification.md            # Invariants, property tests, fuzzing, microbench discipline
└── scripts/
    ├── proptest.ts / .py / .rs    # Property-test scaffolds (fast-check / Hypothesis / proptest)
    └── bench.ts / .py / .rs       # Microbench scaffolds (tinybench / pytest-benchmark / criterion)
```

## Why this exists

Most "data structures" references stop at "here's a BST, here's a hash table." This skill goes further:

- **Translates user intent into a structure + algorithm pairing.** Decision tables map operations and access patterns to canonical picks, with a fallback and a named trap for each.
- **Treats the stdlib as the default.** `HashMap`, `BTreeMap`, `priority_queue` — beating them is a project, not a function. Custom containers are reserved for what the stdlib provides poorly: cache layout, on-disk format, concurrency model, persistence.
- **Language-portable.** Pseudocode + idiom notes for C / C++ / Rust / Go / Java / Python / TypeScript. Calls out gotchas (Python `heapq` is min-only; Rust `BinaryHeap` is max; Java `PriorityQueue` is min by natural order; etc.).
- **Hardware-aware.** L1/L2/L3/DRAM/NVMe/network latency ratios drive structure choice as much as Big-O. SoA vs. AoS, cache lines, branch prediction, allocator behavior — all live alongside the code.
- **Verifiable.** Property-test scaffolds use the oracle pattern (test candidate against a trivially-correct reference) plus invariant checks after every op. Microbench scaffolds sweep working-set sizes and key distributions, defeat DCE, and report median + dispersion.

## Scope

Includes:

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

Algorithms (the central utility — see [`references/algorithms.md`](references/algorithms.md)):

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

## Install

### Claude Code (local)

The skill loads when its directory lives at `~/.claude/skills/<name>/` (or wherever Claude Code's skill loader points). If you already have the convention of project-checked-in skills with symlinks (e.g., `~/.claude/skills/<name> -> ../.agents/skills/<name>`), mirror it:

```bash
# Clone the repo
git clone https://github.com/<you>/dsa-pro.git ~/Projects/dsa-pro

# Symlink into the Claude skills location
ln -s ~/Projects/dsa-pro ~/.claude/skills/dsa-pro

# Verify Claude Code sees it
claude --print "list available skills" 2>/dev/null | grep dsa-pro
```

### skills.sh (Vercel registry)

Once published to GitHub, submit via the [skills.sh](https://skills.sh) registry. The `SKILL.md` frontmatter conforms to the registry schema (`name`, `description`, `license`, `metadata.author`, `metadata.version`, `metadata.triggers`).

## When the skill triggers

The skill self-selects when a task involves any of: storing, indexing, searching, sorting, traversing, batching, ranking, joining, deduplicating, streaming — *and* the answer is not a one-liner. See [`SKILL.md`](SKILL.md) for the full trigger list.

## Contributing

Pull requests welcome. Conventions:

- Pseudocode is the canonical form; language-specific notes call out the stdlib name + gotcha.
- Every structure entry must include invariants, complexity, when-to-use, when-not, language idiom notes, production traps.
- New algorithms come with a recognizable problem shape (the "this looks like" entry in [`references/algorithms.md`](references/algorithms.md)).
- Scaffolds in `scripts/` must use the oracle pattern (proptest) or working-set / distribution sweeps (bench).

## License

MIT. See [`LICENSE`](LICENSE).
