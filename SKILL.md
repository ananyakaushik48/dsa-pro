---
name: dsa-pro
description: Pick and implement data structures + algorithms at production grade. Structures - arrays, linked lists, balanced trees (AVL/red-black/treap), B/B+/LSM trees, segment / Fenwick / persistent trees, heaps (binary/d-ary/pairing/Fibonacci), hash tables (open addressing, Robin Hood, hopscotch, cuckoo), graphs (CSR/list/matrix), tries (HAMT, radix), probabilistic (Bloom, Cuckoo filter, Count-Min, HyperLogLog), union-find, persistent/immutable, lock-free/concurrent. Algorithms - sorts (intro/pdq/Timsort/radix/external), selection, graph (Dijkstra/Bellman-Ford/A*/Tarjan/Hopcroft-Karp/Dinic), strings (KMP/Z/Aho-Corasick/Manacher/suffix automaton), DP, number theory, geometry, bit hacks, streaming. Use when designing or reviewing code that stores, indexes, searches, sorts, traverses, batches, ranks, or streams data; choosing between Map/Set/PriorityQueue and the shape is unclear; picking in-memory vs on-disk indexes; or "make it faster" arrives without a clear culprit.
license: MIT
metadata:
  author: https://github.com/hydrazine
  version: "0.1.0"
  domain: language-agnostic
  triggers: data structure, algorithm, complexity, Big-O, container choice, index, cache, queue, hot path, Map, Set, PriorityQueue, heap, hash, tree, graph, trie, sort, search, traverse, BFS, DFS, Dijkstra, Bellman-Ford, A*, KMP, Aho-Corasick, dynamic programming, Bloom filter, HyperLogLog, LSM, B-tree, B+ tree, lock-free, persistent data structure
  role: specialist
  scope: design+implementation
  output-format: code+pseudocode
  related-skills: rust-engineer, python-pro, golang-pro, typescript-pro, test-master, benchmark
---

# CS Data Structures & Algorithms

A senior-engineer reference for picking and implementing the right data-structure + algorithm combination for any problem, across any language or hardware target. Optimized for "translate a fuzzy user request into a production-grade choice, then implement it correctly the first time."

## When to invoke

Invoke when the task involves storing, indexing, searching, sorting, traversing, batching, ranking, joining, deduplicating, or streaming data — and the answer is not a one-liner. Specifically:

- Choosing between `Map` / `Set` / `PriorityQueue` and the right *shape* (insertion-order? sorted? concurrent? on-disk? approximate?) isn't obvious from the call site.
- Designing an index, cache, queue, batcher, scheduler, or hot data path.
- "Make it faster" lands without a named culprit and the suspect is a container or traversal pattern.
- The problem name maps to a known algorithm (shortest path, k-th element, top-K, substring search, range sum, union of intervals, count distinct, etc.).
- Reviewing code that holds a quadratic loop, naive scan, growing memory, or O(n) operation on a hot path.

If the task is `arr.push(x)` or `Object.keys(o)`, this skill is overkill.

## Mental model

1. **Specify access patterns *before* naming a structure.** State the operations (point / range / order / membership / topology / rank / streaming), workload mix (read/write/update ratios), expected N, working-set vs. cold-set, concurrency model, persistence and crash semantics. *Then* pick. Naming a tree before stating the operations is backwards.
2. **Constants and the memory hierarchy dominate Big-O at the sizes you actually run.** A flat `Vec` / `ArrayList` / `slice` beats a balanced tree well past N = 10⁴ for many workloads. Approximate latencies: L1 ≈ 4 cycles, L2 ≈ 12, L3 ≈ 40, DRAM ≈ 100–300, NVMe ≈ 10⁵, network ≈ 10⁶⁺. Optimize for the hottest layer the data lives in.
3. **Reach for the stdlib first.** `std::unordered_map`, Python `dict`, JS `Map`, Java `HashMap`, Rust `HashMap`, Go `map` already ship battle-tested open-addressing / Robin Hood / etc. Beating them is a project, not a function — pick custom only when you can *name* what the stdlib lacks (specific access pattern, layout, allocator, on-disk format, concurrency).
4. **Encode invariants as property tests, not as comments.** Every non-trivial structure has invariants (BST ordering, heap property, hash load factor bounds, AVL balance, LSM level monotonicity, persistent-tree structural sharing). Property tests against a reference catch refactor regressions that example-based tests miss. See [`references/verification.md`](references/verification.md).
5. **Measure in the target environment.** A microbench in your prod-shaped hardware / JIT / allocator settles arguments that Big-O reasoning never can. Same structure can run 10× faster or slower with different key distributions, cardinalities, or working-set sizes.

## Workflow

1. **Restate the problem as `<operations> + <access pattern> + <N> + <constraints>`.** Example: "read-heavy ordered point + range lookups, ~10 M 64-bit keys, in-process, single writer many readers, must survive process crash" — not "I need a tree." This step kills half the wrong answers before they're written.
2. **Consult [`references/decision-tree.md`](references/decision-tree.md)** for the canonical pick. Note the *fallback* and the *trap*.
3. **Look up the structure in [`references/catalogue.md`](references/catalogue.md)** for invariants, complexities, language-specific stdlib names, and production gotchas.
4. **Find the algorithm in [`references/algorithms.md`](references/algorithms.md)** when traversing, transforming, searching, ranking, or aggregating.
5. **Implement.** Start from a stdlib container. Roll custom only when you can name what the stdlib lacks.
6. **Verify** with property tests against a reference implementation. See [`references/verification.md`](references/verification.md) and `scripts/proptest.{ts,py,rs}`.
7. **Benchmark** with the harnesses in `scripts/bench.{ts,py,rs}`. Always report the access pattern alongside numbers — same structure ten times faster or slower depending on key distribution / working set.

## File map

| When | Open |
|------|------|
| Picking the right structure for a stated workload | [`references/decision-tree.md`](references/decision-tree.md) |
| Need invariants / Big-O / language stdlib name / production traps for a specific structure | [`references/catalogue.md`](references/catalogue.md) |
| Need an algorithm template (sort, search, graph, string, DP, geometry, bit, stream) | [`references/algorithms.md`](references/algorithms.md) |
| About to ship a custom structure — what to test and how | [`references/verification.md`](references/verification.md) |
| Need a property-test or microbench scaffold | `scripts/proptest.{ts,py,rs}`, `scripts/bench.{ts,py,rs}` |

Pseudocode in references uses a single canonical form; language-specific notes call out stdlib names and gotchas (e.g., Python `heapq` is min-only — negate for max; C++ `std::priority_queue` is max by default; Rust `BinaryHeap` is max; Java `PriorityQueue` is min by natural order). Skip past anything obvious; the references are dense by design.
