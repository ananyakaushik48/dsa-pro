# Algorithms

The translation layer between "what the user described" and "a production-grade combination of structures + steps." Front-loaded with pattern recognition — most user questions match a known shape; recognize the shape first, then write code.

## Contents

1. [Problem → pattern (cheatsheet)](#problem--pattern-cheatsheet)
2. [Sorting](#sorting)
3. [Selection (k-th element)](#selection-k-th-element)
4. [Searching](#searching)
5. [Graphs: traversal](#graphs-traversal)
6. [Graphs: shortest path](#graphs-shortest-path)
7. [Graphs: MST, SCC, topology, bridges](#graphs-mst-scc-topology-bridges)
8. [Graphs: flow, matching](#graphs-flow-matching)
9. [Strings](#strings)
10. [Dynamic programming](#dynamic-programming)
11. [Number theory](#number-theory)
12. [Geometry](#geometry)
13. [Bit tricks](#bit-tricks)
14. [Streaming / online](#streaming--online)
15. [Randomization](#randomization)

---

## Problem → pattern (cheatsheet)

| Shape of the problem | Pattern |
|----------------------|---------|
| "Count / sum of subarrays satisfying P over an array" | Prefix sum + hashmap |
| "Longest / shortest contiguous subarray satisfying P" | Two pointers / sliding window |
| "k-th smallest / largest" (one-shot) | Quickselect O(n) |
| "k-th smallest / largest (top-K)" from stream | Min-heap of size K |
| "Pairs (i, j) with i < j satisfying P over array" | Merge sort with count, BIT, or two pointers if sorted |
| "Range sum / min / max under point updates" | Fenwick (sum) / Segment tree (others) |
| "Range update + range query" | Segment tree with lazy propagation |
| "Static range min/max, many queries" | Sparse table (O(1) query) |
| "Sliding window min / max" | Monotonic deque |
| "Next greater / smaller element" | Monotonic stack |
| "Substring search, 1 pattern" | KMP / Z-algorithm |
| "Substring search, many patterns over many texts" | Aho-Corasick |
| "Palindromes in a string" | Manacher's |
| "Suffix problems (LCS, distinct substrings, …)" | Suffix array + LCP, or suffix automaton |
| "Membership with FP OK, FN never" | Bloom filter (or Cuckoo filter with deletes) |
| "Approximate distinct count over stream" | HyperLogLog |
| "Approximate top-K / heavy hitters in stream" | Count-Min sketch + min-heap, or Misra-Gries |
| "Approximate percentiles over stream" | t-digest |
| "Median of a stream" | Two heaps (max for lower half, min for upper half) |
| "Are these two elements connected? (offline)" | Union-Find (DSU) |
| "Number of islands / connected components" | DSU or BFS/DFS |
| "Shortest path, non-negative weights" | Dijkstra with binary heap (or d-ary for dense) |
| "Shortest path, may have negative weights" | Bellman-Ford / SPFA |
| "All-pairs shortest path, V ≤ ~500" | Floyd-Warshall |
| "Heuristic-guided shortest path" | A* with admissible heuristic |
| "Topological order of a DAG" | Kahn's (BFS over in-degree) or DFS post-order reverse |
| "Cycle in directed graph" | DFS coloring (white/gray/black) or DSU on undirected |
| "Strongly connected components" | Tarjan or Kosaraju |
| "Bridges / articulation points" | Tarjan's low-link DFS |
| "Min spanning tree" | Kruskal (sparse) or Prim (dense) |
| "Max flow / min cut" | Dinic's (general) or Edmonds-Karp (small) |
| "Bipartite matching" | Hopcroft-Karp |
| "Assignment / weighted bipartite matching" | Hungarian algorithm |
| "Closest pair of points" | Sweep line / divide & conquer |
| "Convex hull" | Andrew's monotone chain or Graham scan |
| "Range geometric queries (2D)" | KD-tree (low D), R-tree, or BIT on coordinates |
| "Versioned / time-travel data structure" | Persistent variant (path-copy, persistent segment tree, HAMT) |
| "Online ranking / leaderboard" | Order-statistic tree, skip list, or `[sortedcontainers.SortedList]` / `BTreeMap` |
| "Online add + median / arbitrary quantile" | Order-statistic tree, or two-heap median |
| "LRU cache" | HashMap + doubly linked list |
| "LFU cache" | HashMap + DLL of DLLs (one DLL per frequency) |
| "Trie pattern: autocomplete, longest-common-prefix" | Trie / radix tree |
| "Range-XOR query on subarrays" | Prefix XOR + hashmap, or trie of binary representations for max-XOR |
| "Diff / similarity between sequences" | DP (LCS / edit distance) or Hunt-Szymanski (long inputs) |
| "Knapsack with capacity ≤ ~10⁵" | 1D DP `dp[w] = max(dp[w], dp[w - w_i] + v_i)` |
| "Coin change / number of ways" | DP, watch order of loops (item-outer for combinations, capacity-outer for permutations) |
| "Number of paths in DAG" | DP on topological order |
| "Game-state minimax" | Memoized DP / α-β pruning |
| "Counting / probability with overlapping subproblems" | DP or inclusion-exclusion |

---

## Sorting

### Comparison sorts

| Sort | Best | Avg | Worst | Stable | In-place | Notes |
|------|------|-----|-------|--------|----------|-------|
| Quicksort (Hoare/Lomuto) | O(n log n) | O(n log n) | O(n²) | No | Yes | Adversarial inputs hit O(n²) — randomize pivot or use median-of-three. |
| Introsort | O(n log n) | O(n log n) | O(n log n) | No | Yes | Quicksort that switches to heapsort at depth limit (2 log n). `std::sort` in C++. |
| Pdqsort | O(n) (sorted) | O(n log n) | O(n log n) | No | Yes | Pattern-defeating quicksort. Rust `sort_unstable`, Boost. |
| Heapsort | O(n log n) | O(n log n) | O(n log n) | No | Yes | Predictable worst case; bad cache behavior. |
| Mergesort | O(n) | O(n log n) | O(n log n) | Yes | No (O(n) aux) | Stable; good for external / linked. |
| Timsort | O(n) | O(n log n) | O(n log n) | Yes | No (O(n) aux) | Adaptive, exploits "runs." Python `sorted`/`list.sort`, Java `Arrays.sort` for objects. |
| Insertion sort | O(n) | O(n²) | O(n²) | Yes | Yes | Best at n ≤ ~16–32; used as base case in introsort/pdqsort. |
| Shell sort | O(n log² n) | O(n^1.3) | O(n²) | No | Yes | Rarely used in production; nice in small / embedded code. |

### Non-comparison sorts

| Sort | Time | Space | Notes |
|------|------|-------|-------|
| Counting sort | O(n + k) | O(n + k) | k = value range. Use for small-range ints. |
| Radix sort (LSD) | O(d · (n + k)) | O(n + k) | d = digits. Stable; uses counting sort per digit. |
| Radix sort (MSD) | O(d · (n + k)) | O(n) recursion | Better for strings. |
| Bucket sort | Avg O(n + n²/k + k) | O(n + k) | Uniform input distribution required for the average. |
| Spreadsort / IPS⁴ | O(n · log_k(n)) | low aux | Hybrid radix; `boost::sort::spreadsort`. |

### External / parallel
- **External merge sort.** Sort chunks that fit in RAM → write sorted runs → k-way merge with a priority queue.
- **Parallel sort.** `std::sort` w/ `std::execution::par` (C++17), Rust `rayon::par_sort`, Java `Arrays.parallelSort`, Go `slices.SortFunc` + worker pool. Useful past ~10⁵ elements with ≥ 4 cores.

### When to pick what

- Stable sort needed → Timsort / mergesort / `std::stable_sort`.
- Predictable worst case → introsort / heapsort.
- Fastest in practice on arbitrary keys → pdqsort.
- Small array (≤ 32) → insertion sort.
- Small-range integers → counting / radix.
- Strings → MSD radix or three-way radix quicksort.
- External or distributed → external merge / sample sort.

### Pseudocode — quickselect-style partition (also used in pdq, intro)

```text
partition(a, lo, hi):
  pivot = a[mid]            # median-of-three for prod
  i = lo - 1
  j = hi + 1
  loop:
    do i = i + 1 while a[i] < pivot
    do j = j - 1 while a[j] > pivot
    if i >= j: return j
    swap(a[i], a[j])
```

---

## Selection (k-th element)

### Quickselect

```text
select(a, lo, hi, k):
  while lo < hi:
    p = partition(a, lo, hi)
    if k <= p: hi = p
    else: lo = p + 1
  return a[lo]
```

O(n) expected, O(n²) worst with bad pivots.

### Median of medians ("BFPRT")
Partitions into groups of 5, finds median of each, recursively finds median-of-medians as pivot. Guarantees O(n) worst-case but with large constants — rarely used in practice.

### Top-K (stream)
Min-heap of size K. Walk stream; on each element, if heap size < K push, else if element > heap min, replace.

### Order-statistic tree
A BST / B-tree augmented with subtree size at each node — `select(k)` in O(log n).
- C++: `__gnu_pbds::tree<...>` with `find_by_order` (libstdc++ extension).
- Python: `sortedcontainers.SortedList` (`.bisect_left` + index).
- Java: no stdlib; use `TreeMap` + a Fenwick if you need rank.

---

## Searching

### Binary search (the canonical bug-prone primitive)

```text
# Lower bound: first index i with a[i] >= key  (or n if none)
lo, hi = 0, n
while lo < hi:
  mid = (lo + hi) >> 1
  if a[mid] < key: lo = mid + 1
  else: hi = mid
return lo
```

- Use **`lo + (hi - lo) / 2`** for languages where `+` can overflow; right shift is fine for unsigned.
- Distinguish `lower_bound` (first `>= key`), `upper_bound` (first `> key`), `equal_range`.
- "Binary search on the answer": when the predicate `f(x)` is monotone, binary-search the answer space — used for scheduling, capacity planning, the "Aggressive Cows" pattern.

### Exponential search
For unbounded / streaming arrays: double the upper bound until `a[hi] ≥ key`, then binary search [hi/2 .. hi]. O(log p) where p is the answer position.

### Ternary search
Find min / max of a unimodal function in O(log n). Floating: stop after ~200 iterations or 1e-9 relative error.

### Fractional cascading
Speed up search across k sorted arrays from O(k log n) to O(k + log n) by maintaining bridge pointers between levels. Heavy machinery — only deploy when k is large.

---

## Graphs: traversal

### BFS

```text
queue = [s]; visited = {s}; dist[s] = 0
while queue not empty:
  u = queue.popleft()
  for v in adj[u]:
    if v not in visited:
      visited.add(v); dist[v] = dist[u] + 1
      queue.append(v)
```

**Use when.** Shortest path in unweighted graph; layer-by-layer processing; bipartite test (alternating coloring).

### DFS (iterative — recursion is for ≤ 10⁴ nodes max; blow stack otherwise)

```text
stack = [(s, iter(adj[s]))]; visited = {s}; enter_order[s] = clock++
while stack:
  u, it = stack[-1]
  v = next(it, None)
  if v is None:
    leave_order[u] = clock++
    stack.pop()
  elif v not in visited:
    visited.add(v); enter_order[v] = clock++
    stack.append((v, iter(adj[v])))
```

**Use when.** Topological sort, SCC, bridges, cycle detection, recursive subtree DP.

### Iterative deepening DFS
DFS with depth limit, increased each round. Use when state space is huge and BFS memory is unaffordable.

### Bidirectional search
Run BFS from source and target alternately; stop when frontiers meet. Cuts search size from O(b^d) to O(b^(d/2)).

---

## Graphs: shortest path

### Dijkstra (non-negative weights)

```text
dist[*] = +inf; dist[s] = 0
pq = MinHeap of (0, s)
while pq:
  d, u = pq.pop()
  if d > dist[u]: continue          # lazy delete trick
  for (v, w) in adj[u]:
    nd = d + w
    if nd < dist[v]:
      dist[v] = nd
      pq.push((nd, v))
```

- Binary heap: O((V + E) log V). d-ary heap: O((V + E) log_d V), good for dense.
- Fibonacci heap: O(E + V log V) — theoretical best, rarely faster in practice.
- **Negative weights → wrong answer.** Use Bellman-Ford or SPFA.

### Bellman-Ford
V-1 passes of relaxing all edges; one more pass to detect negative cycles.

```text
for i in 1..V-1:
  for (u, v, w) in edges:
    if dist[u] + w < dist[v]:
      dist[v] = dist[u] + w
# Extra pass: if anything relaxes, negative cycle reachable.
```

O(V · E). Tolerates negative weights; reports negative cycles.

### SPFA (Bellman-Ford with a queue)
Average much faster than Bellman-Ford, worst case still O(V·E). Vulnerable to adversarial graphs — has fallen out of fashion in competitive programming since the 2018+ killer-cases were published; use Dijkstra (or Bellman-Ford) for hardened code.

### Floyd-Warshall (all-pairs)

```text
for k in 0..V:
  for i in 0..V:
    for j in 0..V:
      if dist[i][k] + dist[k][j] < dist[i][j]:
        dist[i][j] = dist[i][k] + dist[k][j]
```

O(V³). Good for V ≤ ~500. Also computes transitive closure (`bool`), min/max bottleneck (replace `+` with `max`), and matrix-style reductions.

### A*
Dijkstra with `g + h` priority where `h` is an *admissible* heuristic (never overestimates true distance). Becomes Dijkstra when `h = 0`, becomes greedy best-first when `g = 0`. Used in pathfinding (Manhattan / Euclidean / landmark heuristics).

### Yen's k-shortest paths
Generate the k shortest *loopless* paths from s to t in O(K · V · (V log V + E)).

### Johnson's all-pairs (sparse, possibly negative)
Bellman-Ford to reweight edges non-negative, then Dijkstra from each source. O(V² log V + V·E).

---

## Graphs: MST, SCC, topology, bridges

### Kruskal's MST

```text
sort edges by weight
dsu = DSU(V)
for (u, v, w) in edges:
  if dsu.union(u, v):
    mst.append((u, v, w))
```

O(E log E). Pair with DSU.

### Prim's MST
Like Dijkstra but using "cheapest edge to the tree" as priority. O((V + E) log V). Better for dense graphs.

### Topological sort

```text
# Kahn's (BFS over in-degree)
indeg = compute in-degrees
queue = [u for u where indeg[u] == 0]
order = []
while queue:
  u = queue.popleft()
  order.append(u)
  for v in adj[u]:
    indeg[v] -= 1
    if indeg[v] == 0: queue.append(v)
if len(order) < V: cycle exists
```

DFS variant: emit nodes in reverse post-order.

### Tarjan's SCC

```text
index = 0; stack = []; on_stack = set(); indices = {}; low = {}
def visit(u):
  indices[u] = low[u] = index; index += 1
  stack.append(u); on_stack.add(u)
  for v in adj[u]:
    if v not in indices:
      visit(v)
      low[u] = min(low[u], low[v])
    elif v in on_stack:
      low[u] = min(low[u], indices[v])
  if low[u] == indices[u]:
    scc = []
    while True:
      w = stack.pop(); on_stack.remove(w); scc.append(w)
      if w == u: break
    yield scc
```

O(V + E). Kosaraju is simpler (two DFSes on G and G^T) but twice the constant.

### Bridges / articulation points (Tarjan)
Same `disc` / `low` DFS — edge (u, v) is a bridge iff `low[v] > disc[u]`; vertex u is an articulation point iff u is the DFS root with ≥ 2 children, or non-root with a child v where `low[v] ≥ disc[u]`.

### 2-SAT
Strongly-connected components of the implication graph: for each clause `a ∨ b`, add `¬a → b` and `¬b → a`. Satisfiable iff no variable shares a SCC with its negation. O(N + M).

---

## Graphs: flow, matching

### Edmonds-Karp (max-flow)
BFS-augmenting on residual graph. O(V · E²). Good for V, E ≤ ~10⁴.

### Dinic's
BFS to build level graph; DFS to push blocking flow. O(V² · E) general; O(E · √V) on unit-capacity / bipartite matching. Default for medium-to-large flow problems.

### Push-relabel (HLPP / FIFO)
O(V² · √E) or O(V³). Beats Dinic on dense max-flow.

### Min-cost max-flow
SPFA (or Bellman-Ford if any negative edges) on a residual graph with potentials. Use Johnson-style reweighting after the first round if you want to switch to Dijkstra for the rest. O(V · E²) generic, O(F · E log V) when flow F is small.

### Bipartite matching
- Hopcroft-Karp: O(E · √V).
- Kuhn (DFS-augmenting): O(V · E), simpler — fine for small graphs.

### Weighted bipartite matching (assignment problem)
Hungarian / Kuhn-Munkres: O(V³). For sparse, use min-cost flow.

### Maximum matching (general graph)
Blossom algorithm (Edmonds): O(V² · E) or O(V³); rarely needed outside competitive programming and matchmaking systems.

---

## Strings

### KMP (single-pattern search)

```text
# Build prefix function (longest proper prefix = suffix)
pi[0] = 0
for i in 1..m-1:
  j = pi[i-1]
  while j > 0 and pat[i] != pat[j]: j = pi[j-1]
  if pat[i] == pat[j]: j += 1
  pi[i] = j

# Search
j = 0
for i in 0..n-1:
  while j > 0 and text[i] != pat[j]: j = pi[j-1]
  if text[i] == pat[j]: j += 1
  if j == m: yield i - m + 1; j = pi[j-1]
```

O(n + m).

### Z-algorithm
`z[i]` = length of longest substring starting at i that matches the prefix. O(n) to compute. Use for pattern matching (concat `pat + sep + text`, scan for `z[i] == m`).

### Rabin-Karp
Rolling hash for substring search; useful for multi-pattern of equal length, plagiarism detection. Cryptographic? No — use only when collisions are not adversarial, or hash with two independent moduli.

### Aho-Corasick (multi-pattern)
KMP generalized to a trie with failure links. Build a finite automaton over all patterns; scan text once in O(n + total pattern length + occurrences).

```text
# Build trie of patterns
# BFS to add failure links: fail[u] = longest proper suffix of path-to-u that's also a node
# scan text following goto / fail edges
```

Use for: log scanning, IDS / IPS, spam-keyword filtering, virus signature matching.

### Manacher's (all palindromic substrings)
O(n) to find the longest palindromic substring; trick is to insert sentinels between characters so odd / even are unified.

### Suffix array
Sorted array of all suffix start positions. Build in O(n log n) (DC3) or O(n) (SA-IS, harder to implement). With the LCP (longest common prefix) array, supports:
- Substring search in O(m log n) (binary search over suffixes).
- Longest common substring of multiple strings.
- Number of distinct substrings: `n·(n+1)/2 - Σ lcp[i]`.

### Suffix automaton
DAG with O(n) states accepting exactly the substrings of S. Build online in O(n). Supports number of distinct substrings, longest common substring, kth-distinct-substring all elegantly.

### Burrows-Wheeler Transform (BWT)
Reversible permutation of S used in bzip2, FM-index (compressed suffix-array search). Look up: BWT, LF-mapping, FM-index, Move-to-Front.

---

## Dynamic programming

### Recognizing DP
The problem has (a) optimal substructure (optimal solution composed of optimal sub-solutions), (b) overlapping subproblems, (c) polynomial state space. Three common state shapes: prefix `dp[i]`, intervals `dp[l][r]`, subsets / bitmask `dp[mask]`.

### Memoization vs. tabulation
Memoization: recursive, lazy, easy to write, allocation overhead. Tabulation: iterative, eager, cache-friendly, harder when ordering isn't obvious. **Default to memoization** for prototyping, switch to tabulation for hot paths.

### Classical patterns

- **0/1 Knapsack.** `dp[w] = max(dp[w], dp[w - w_i] + v_i)`; loop items outer, capacity descending inner.
- **Unbounded knapsack / coin change (min coins).** `dp[w] = min(dp[w], dp[w - w_i] + 1)`; capacity ascending.
- **Coin change (#ways).** Loop items outer, capacity ascending — order matters: items-outer gives combinations, capacity-outer gives permutations.
- **LIS (longest increasing subsequence).** O(n²) DP, or O(n log n) with a "patience" list + binary search (Hunt-Szymanski).
- **LCS (longest common subsequence).** `dp[i][j]` 2D — O(n·m).
- **Edit distance.** Same shape as LCS — O(n·m); Hirschberg's reduces space to O(min(n, m)).
- **Matrix chain multiplication.** Interval DP `dp[l][r]` — O(n³).
- **Bitmask DP.** State = `(subset, current_position)`. TSP O(2^n · n²), Hamiltonian path counting O(2^n · n²).
- **Tree DP.** DFS post-order; `dp[u] = f(dp[children])`. Re-rooting technique computes `dp` for every node as root in O(n) total.
- **Digit DP.** State = `(position, tight, leading_zero, ..., extra)` — counts numbers ≤ N satisfying digit constraints.
- **Profile / broken profile.** Tile a grid with dominoes — O(2^cols · rows · transitions).

### Optimizations

- **Knuth's optimization.** Interval DP with `opt[l][r] = argmin_k dp[l][k] + dp[k+1][r]` monotone — drops O(n³) to O(n²).
- **Convex hull trick (CHT) / Li Chao tree.** When transitions are line-evaluations and the optimal line changes monotonically.
- **Divide & conquer DP optimization.** When `opt(l, r)` is monotone in r — O(n² → n log n).
- **SOS (Sum over Subsets) DP.** `f[mask] = Σ over submasks of mask of g[submask]` in O(N · 2^N).
- **Aliens trick (lambda optimization).** Convexity in k for "exactly k segments" problems.

### Memory reduction
Rolling arrays — keep only the rows / cols needed for the current transition (LCS, knapsack, edit distance all collapse to O(min) space).

---

## Number theory

```text
# GCD (Euclid)
gcd(a, b) = a if b == 0 else gcd(b, a mod b)

# Extended GCD (a·x + b·y = gcd(a, b))
extgcd(a, b):
  if b == 0: return (a, 1, 0)
  (g, x1, y1) = extgcd(b, a mod b)
  return (g, y1, x1 - (a / b) * y1)

# Modular exponentiation
modpow(b, e, m):
  r = 1; b = b mod m
  while e > 0:
    if e & 1: r = r * b mod m
    b = b * b mod m
    e >>= 1
  return r

# Modular inverse: only when gcd(a, m) == 1
# - prime m: a^(m-2) by Fermat
# - composite m: extgcd
```

- **Sieve of Eratosthenes.** O(n log log n). For n ≤ 10⁷.
- **Linear sieve.** O(n), gives smallest prime factor — useful for fast factorization.
- **Miller-Rabin.** Deterministic for 64-bit ints with bases {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37}. Probabilistic otherwise.
- **Pollard's rho.** Factor n in O(n^¼) expected — pair with Miller-Rabin.
- **CRT.** Reconstruct x mod (m₁·m₂) from x mod m₁ and x mod m₂ when gcd(m₁, m₂) = 1.
- **Euler's totient φ(n)** = `n · Π (1 - 1/p)` over distinct primes p | n.

---

## Geometry

```text
# Cross product (CCW test): > 0 left turn, < 0 right turn, == 0 colinear
cross(o, a, b) = (a.x - o.x)*(b.y - o.y) - (a.y - o.y)*(b.x - o.x)
```

- **Convex hull — Andrew's monotone chain.** O(n log n). Sort points by (x, y), build lower then upper hull.
- **Point-in-polygon.** Ray casting (works for non-convex); winding number (handles self-intersecting).
- **Segment intersection.** Sweep-line (Bentley-Ottmann) in O((n + k) log n) for k intersections.
- **Closest pair of points.** Divide & conquer in O(n log n) or sweep with a sorted set.
- **Rotating calipers.** Diameter / width / closest-pair of convex hull in O(n).
- **Half-plane intersection.** Sort by angle, sweep with a deque.
- **KD-tree nearest neighbor.** O(log n) expected in low D.

**Floating-point traps.** Use integer arithmetic where possible. When using doubles, define `EPS = 1e-9` for *small* coordinates; scale up for large. Avoid `==` on floats — use `abs(a - b) < eps`.

---

## Bit tricks

```text
popcount(x)          # std builtins: __builtin_popcountll, x.count_ones()
ctz(x)               # trailing zeros: index of lowest set bit
clz(x)               # leading zeros: useful for log2 floor
x & -x               # isolate lowest set bit (also called "lowbit"; Fenwick uses this)
x & (x - 1)          # clear lowest set bit (Kernighan's count: loops popcount times)
((x | (x - 1)) + 1)  # next permutation with same popcount (Gosper's hack)
```

- **XOR tricks.** `a ^ a == 0`; `0 ^ a == a` → find the single element appearing odd times by XOR-ing the whole array.
- **Subset iteration.** For each submask of `mask`: `s = mask; while s > 0: ...; s = (s - 1) & mask`.
- **Power-of-two check.** `(x & (x - 1)) == 0`.
- **Fast modular reduction.** Power-of-two: `x & (m - 1)` instead of `x % m`.
- **Set bit count via 64-bit word.** `__builtin_popcountll` maps to single `POPCNT` instruction on x86 (since Nehalem) and on aarch64.

---

## Streaming / online

- **Reservoir sampling (Algorithm R).** k-out-of-stream uniform sample:
  ```text
  for i in 0..k: R[i] = stream[i]
  for i in k..n: j = randint(0, i); if j < k: R[j] = stream[i]
  ```
  O(n) time, O(k) space.
- **Algorithm L.** Same result, fewer RNG calls — skip ahead by `floor(log(rand()) / log(1 - w))`.
- **Weighted reservoir (Chao / A-Res).** O(n) for weighted k-sample.
- **Moving statistics.** Sliding-window sum: add new, subtract old. Sliding-window min/max: monotonic deque in O(n) total.
- **Heavy hitters (Misra-Gries).** Find all elements appearing > n/k times in one pass, O(k) space.
- **Count-distinct (HyperLogLog).** See [`catalogue.md`](catalogue.md#probabilistic--sketches).
- **Frequency estimation (Count-Min).** Two-pass: estimate then verify.
- **Online median.** Two heaps; size balance ≤ 1.
- **Welford's algorithm.** Numerically stable running mean / variance:
  ```text
  n = 0; mean = 0; M2 = 0
  for x in stream:
    n += 1; d = x - mean; mean += d / n; d2 = x - mean; M2 += d * d2
  var = M2 / (n - 1)
  ```

---

## Randomization

- **Fisher-Yates shuffle.** `for i in n-1..1: j = randint(0, i); swap(a[i], a[j])`. O(n).
- **Generate random subset of size k.** Fisher-Yates partial — only shuffle the first k positions.
- **Weighted random pick.** Build prefix-sum array of weights; binary-search a uniform `[0, total)` draw. Alias method (Vose) gives O(1) per draw with O(n) precompute.
- **Random permutation of a stream of unknown size.** Reservoir sampling with k = entire stream.
- **Las Vegas vs. Monte Carlo.** Las Vegas always correct, runtime random (quicksort with random pivot). Monte Carlo runtime bounded, output may be wrong with bounded probability (Miller-Rabin, Rabin-Karp).
- **Randomized algorithms in production** — seed deterministically per run (for reproducibility) but cycle the seed across runs so adversaries can't exploit one bad seed.
