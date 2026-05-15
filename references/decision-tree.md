# Decision Tree

Fast lookup. Each row: **want** → **reach for** → **fall back to** → **trap**. Match the *want* row to your access pattern, not to a structure name.

## Single-process in-memory containers

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Sequence, mostly tail append | `Vec` / `ArrayList` / slice | Linked list | Stable refs across pushes — use slot map / arena. |
| FIFO, bounded | Ring buffer (`ArrayDeque` / `VecDeque`) | Linked list | Power-of-two cap → `& (cap-1)` instead of `% cap`. |
| FIFO, unbounded | `VecDeque` / Java `ArrayDeque` / Go channel | Linked list | `std::queue<int>` over `std::deque<int>` is fine; `std::list<int>` is a trap. |
| LIFO | `Vec` / `ArrayList` (push/pop tail) | — | None. |
| Sliding-window min / max | Monotonic deque (`ArrayDeque`) | Multiset (`std::multiset`) | Monotonic deque is O(n) total; multiset is O(n log n). |
| Top-K from stream | Min-heap of size K | Sort then trim | Bigger constant factor on heap when K = n — just sort. |
| Median of stream | Two heaps (max for lower, min for upper) | Order-statistic tree | Heaps don't support arbitrary quantiles — use OS-tree. |
| Frequency count by key | `HashMap<K, u32>` / `Counter` | Sorted map if you need ordered iteration | `defaultdict(int)` (Python) skips the "if key in d" dance. |
| LRU cache | `LinkedHashMap` (Java) / `OrderedDict.move_to_end` (Python) / hashmap + DLL (others) | `lru-cache` crate / `functools.lru_cache` | Don't mutate the DLL without updating the hashmap. |
| LFU cache | HashMap + DLL of DLLs (one DLL per frequency) | Heap | Heap-based LFU is O(log n) per op; DLL approach is O(1) but more code. |

## Key-value lookup

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| O(1) point lookup, no ordering | `HashMap` / `dict` / `Map` | — | Hash floods on user input → use SipHash-keyed hashmap (Python / Rust default) or randomize seed per process. |
| O(1) lookup + insertion-order iteration | Python `dict` / JS `Map` / Java `LinkedHashMap` / Rust `IndexMap` | — | Inserts that touch existing keys *don't* reorder in Python; use `move_to_end` if you need LRU. |
| O(log n) ordered point + range | `BTreeMap` (Rust) / `TreeMap` (Java) / `std::map` (C++) / `sortedcontainers.SortedDict` (Python) | Skip list | Java `TreeMap` is red-black, not B-tree. |
| Bidirectional map (k↔v) | `bimap` crate / `BiMap` (Guava) | Two HashMaps you maintain by hand | Keeping two maps in sync is a perennial bug source. |
| Multi-map (multiple values per key) | `HashMap<K, Vec<V>>` or `multimap` lib | — | `defaultdict(list)` in Python. |
| Map keys are integers in a known small range | Direct array indexed by key | HashMap | Beats HashMap by 5–20× when applicable. |
| Concurrent map, read-heavy | RCU / arc-swap snapshot | `DashMap` (Rust) / `ConcurrentHashMap` (Java) | Cliff Click's `NonBlockingHashMap` is rarely worth the dependency. |
| Concurrent map, write-heavy | Lock-striped (`DashMap`, `ConcurrentHashMap`) | Sharded `Mutex<HashMap>` | Lock-free maps are tricky — sharded is good enough almost always. |
| Persistent / immutable map | HAMT — Clojure / Scala / Rust `im` / Haskell `unordered-containers` | Path-copy RB tree | Bulk updates: use transient/builder; otherwise allocator pressure dominates. |

## Set membership

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Exact set | `HashSet` / `set` / `BTreeSet` | — | C++ `unordered_set` is slow vs `std::set` for tiny N. |
| Small dense int set | Bitset | HashSet | Iterating uses `ctz`/`__builtin_ctz` to skip zero bits — naive iteration is O(N). |
| Approximate membership, FN never, FP OK | Bloom filter | Cuckoo filter (with deletes) | Size m / hash count k from expected n and target FPR. |
| Approximate membership w/ deletes | Cuckoo filter | Counting Bloom | Insert can fail (eviction loop limit) → rebuild. |
| Approximate cardinality | HyperLogLog | Linear Counting (small n) | ~0.81% standard error at any cardinality with 12 KiB. |

## Range queries

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Range sum + point update | Fenwick (BIT) | Segment tree | 1-indexed in canonical impl. |
| Range min / max + point update | Segment tree | Sparse table (static only) | Sparse table is O(1) query but immutable. |
| Range update + range query | Segment tree with lazy propagation | Two Fenwicks for affine ops | Lazy push-down ordering is #1 bug source. |
| 2D range sum, static | 2D prefix sum | 2D BIT | 2D BIT scales to ~10⁶ × 10⁶ cells. |
| 2D range sum, updates | 2D BIT / 2D segment tree | Wavelet tree (k-th queries) | 2D BIT memory is O(n²) — sparse if many empty cells. |
| Static range min/max, dense queries | Sparse table | Segment tree | O(n log n) build, O(1) query. |
| K-th smallest in range | Persistent segment tree / wavelet tree | Merge-sort tree | Persistent: O(log n) query, O((n + U) log n) memory. |

## Strings

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Substring search, 1 pattern | KMP / Z-algorithm | Boyer-Moore (huge alphabet) | `str.find` / `String.indexOf` already uses one of these. |
| Substring search, many patterns | Aho-Corasick | KMP in loop | Build the trie once, scan many texts. |
| Prefix queries / autocomplete | Trie / radix tree | Sorted list + binary search | Trie wins when alphabet is small. |
| Palindrome queries | Manacher's | Hashing + binary search | Manacher's is O(n) for *all* palindromic centers. |
| Suffix queries (LCS, distinct substrs) | Suffix array + LCP | Suffix automaton | SA is more compact; automaton is more elegant. |
| Edit distance / diff | Wagner-Fischer DP (small) | Hunt-Szymanski / Myers (large) | `git diff` uses Myers — adapt for production long-text diffs. |
| Approximate matching | BK-tree on Levenshtein | Bitap (small patterns ≤ 64) | BK-tree is excellent for ≤ 10⁶ words; for larger, build an n-gram index first. |

## Graph problems

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Shortest path, unweighted | BFS | Dijkstra | Don't use Dijkstra when all weights are 1 — wastes a heap. |
| Shortest path, non-negative weights | Dijkstra w/ binary heap | d-ary heap (dense) | Negative weights → wrong answer; switch to Bellman-Ford. |
| Shortest path, negative weights allowed | Bellman-Ford | SPFA (cautiously) | SPFA has known adversarial cases — Dijkstra after Johnson reweighting is safer at scale. |
| All-pairs shortest path | Floyd-Warshall | Johnson's (sparse) | V ≤ ~500 for FW. |
| Pathfinding with heuristic | A* | Dijkstra | h must be admissible — never overestimates. |
| MST | Kruskal + DSU (sparse) | Prim (dense) | Sort edges once; DSU handles unions. |
| SCC | Tarjan | Kosaraju | Tarjan one pass, Kosaraju two passes. |
| Topological order | Kahn's BFS | DFS post-order reverse | Kahn detects cycles by leftover nodes; DFS detects by back-edges. |
| 2-SAT | SCC on implication graph | — | Each clause `a ∨ b` ⇒ `¬a → b`, `¬b → a`. |
| Max flow | Dinic's | Push-relabel (dense) | Edmonds-Karp is simpler but slower past ~10⁴ edges. |
| Bipartite matching | Hopcroft-Karp | Kuhn (small) | Kuhn is `O(V·E)` but trivially short — fine for V ≤ 1000. |
| Assignment / weighted match | Hungarian | Min-cost flow | Hungarian is O(V³). |
| Connectivity (offline) | Union-Find | — | Doesn't support split — use Euler-tour trees if you need dynamic disconnect. |

## On-disk / persistence

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Read-heavy OLTP index | B+ tree | LSM | Write amplification under point updates. |
| Write-heavy index / time-series | LSM (RocksDB / Cassandra) | B+ with WAL | Compaction is *the* operational concern. |
| Append-only log + crash-safety | WAL + checksums | Storage engine's built-in WAL | `fsync` is slow; group commit if latency allows. |
| Snapshots / time-travel | COW B-tree (btrfs / ZFS / APFS) | MVCC with version chain | GC of dead versions matters. |
| Block store dedup | Content-addressed (BLAKE3 / xxh3) | Rolling hash + chunking (rsync, restic) | Choose chunker (FastCDC) for the data shape. |

## Streaming / approximate

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Distinct count over big stream | HyperLogLog | Linear Counting (n small) | Merge HLLs by elementwise max — preserves accuracy. |
| Frequency estimate | Count-Min Sketch | Misra-Gries | Pair with min-heap for top-K. |
| Percentiles over stream | t-digest | Greenwald-Khanna | t-digest is tighter at tail percentiles; GK is better in the middle. |
| Sliding-window distinct count | Sliding-window HLL | Exact with a hashmap + linked list | Decay or windowed reset; can't subtract from HLL exactly. |
| Heavy hitters | Misra-Gries | Count-Min + heap | Pick by stream characteristics — Misra-Gries gives a *superset* of heavy hitters; verify with a second pass. |

## Special access patterns

| Want | Reach for | Fall back | Trap |
|------|-----------|-----------|------|
| Lots of versions / undo | Persistent variant (path-copy) | Snapshot-on-write | Versioning a HashMap → HAMT. Versioning a segment tree → persistent segment tree. |
| Functional programming / immutable | HAMT / RRB-tree / finger tree | Defensive copy on every write | Bulk updates: use transients. |
| Real-time / hard latency | Worst-case O(log n) (RB / AVL / B-tree) | Avoid amortized (splay, hash table without bounded probe) | Splay's amortized O(log n) hides O(n) worst-case per op. |
| Many readers, rare writer | RCU / arc-swap | RwLock | RwLock starves writers under read load. |
| One writer, many readers | Triple-buffer / SeqLock | atomic-pointer swap | SeqLock readers may retry — bound the retries. |

## Quick sanity checks before you implement

- "Is this just `Map<K, List<V>>`?" — 80% of the time, yes.
- "Could this be a prefix sum?" — every fixed-window aggregate problem.
- "Could this be sorted then two-pointer?" — pair-sum, triplet-sum, intervals.
- "Is the answer monotone in some parameter?" — binary-search on the answer.
- "Are the keys integers 0..N?" — direct array beats HashMap.
- "Do I really need ordering?" — most ordered-map uses are mis-specs; HashMap is faster.
- "Am I picking a tree because I learned it in school?" — usually a HashMap or sorted array works.
