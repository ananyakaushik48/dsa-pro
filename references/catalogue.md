# Catalogue

Family-by-family reference. Each entry: **invariants** (the property the structure must maintain), **operations + complexity**, **when to use / when not to**, **language stdlib pointers**, **production traps**.

Skim the table of contents — most structures have a one-liner in [`decision-tree.md`](decision-tree.md); only open this file when you need the *why*.

## Contents

1. [Contiguous storage](#contiguous-storage)
2. [Linked structures](#linked-structures)
3. [Balanced search trees (in-memory)](#balanced-search-trees-in-memory)
4. [Range trees](#range-trees)
5. [Disk-backed / write-heavy trees](#disk-backed--write-heavy-trees)
6. [Heaps and priority queues](#heaps-and-priority-queues)
7. [Hash tables](#hash-tables)
8. [Graphs](#graphs)
9. [Tries](#tries)
10. [Probabilistic / sketches](#probabilistic--sketches)
11. [Disjoint-set (union-find)](#disjoint-set-union-find)
12. [Persistent / immutable](#persistent--immutable)
13. [Concurrent / lock-free](#concurrent--lock-free)
14. [Spatial](#spatial)
15. [Text-edit specific](#text-edit-specific)

---

## Contiguous storage

### Dynamic array (`Vec` / `ArrayList` / slice)

**Invariants.** Contiguous backing of capacity ≥ length; growth factor ≥ 1.5 (1.6–2.0 typical) for O(1) amortized push. **Ops.** Random access O(1); push/pop tail O(1) amortized; insert/erase mid O(n); search O(n). **Use when.** Default for sequences. Cache-friendly, prefetcher-loved, vectorizable. **Avoid when.** Frequent mid-insert/erase (use linked list or gap buffer). Need stable references across pushes (use arena or slot map). **Language.**

- C++: `std::vector<T>`. Growth 1.5 on libstdc++, 2.0 on MSVC. `vector<bool>` is a packed bitset, not an array of `bool`.
- Rust: `Vec<T>`. `with_capacity(n)` to preallocate.
- Go: `[]T`. Growth ~2× under cap 1024, then ~1.25×. `make([]T, 0, n)` to preallocate.
- Java: `ArrayList<T>`. Growth 1.5. `ensureCapacity(n)`.
- Python: `list`. Over-allocation ≈ `9/8 · n + (3|6)`. Use `array.array('i', ...)` for unboxed ints.
- JS: `Array`. V8 transitions between packed-SMI / packed-double / holey / dictionary; assign in order to stay packed.

**Traps.** Mid-removal is O(n); growing while iterating invalidates iterators/refs (UB in C++); array-of-structs is bad for cache when you only touch one field — prefer struct-of-arrays.

### Ring buffer / circular buffer

**Invariants.** Fixed-capacity backing; `(head + count) mod cap == tail`; never both empty and full ambiguous (use a count or sentinel slot). **Ops.** Push/pop both ends O(1). Random access O(1) via `(head + i) mod cap`. **Use when.** Bounded queue (network buffers, audio frames, log buffers, work-stealing deques). **Avoid when.** Unbounded growth. Variable-size elements (use byte ring with length prefixes or a separate index ring). **Traps.** Power-of-two capacity lets you replace `% cap` with `& (cap-1)` (single cycle vs 30+ for `%`). Use atomic head/tail for SPSC lock-free.

### Deque (double-ended queue)

**Invariants.** Push/pop on both ends O(1) amortized. **Implementations.** Block-list (C++ `std::deque`, ~64 KiB blocks) or ring buffer with growth (Rust `VecDeque`). **Use when.** Sliding window, BFS frontier, monotonic deque (range-max / range-min in O(n)). **Traps.** C++ `deque` has *very* slow iteration vs `vector`; benchmark before assuming. Rust `VecDeque` random access is fast but not contiguous — no `&[T]` view.

### Columnar / SoA (struct-of-arrays)

**Invariants.** Field `i` of all rows in a single contiguous array; index `i` aligns across columns. **Ops.** Whole-column scan touches only that column's bytes; SIMD-friendly. **Use when.** Analytics, ECS in game engines, anything that scans a subset of fields per pass. **Avoid when.** You always touch all fields together (then AoS wins cache-line-wise). **Traps.** Inserts must update every column atomically; consider an op log per column with periodic compaction.

### Packed bitset / bit vector

**Invariants.** Bit `i` lives in word `i / W` at offset `i mod W`. **Ops.** Set/clear/test O(1); popcount O(n/W); rank/select O(1) with auxiliary structures. **Use when.** Membership of small dense integer domains, sieves, occupancy maps, transitive closure. **Language.** C++ `std::bitset<N>` (fixed) / `boost::dynamic_bitset`; Rust `bit-vec`/`bitvec`; Python `int` (bit-twiddle on a big int) or `bitarray` package. **Traps.** Iterating set bits naively is O(N); use `_BitScanForward` / `__builtin_ctz` / `u64::trailing_zeros` to jump to next set bit.

### Slot map / generational arena

**Invariants.** Keys are `(index, generation)` pairs; on deletion the slot's generation increments — stale keys reject correctly. **Ops.** Insert / get / remove all O(1). Iteration over occupied slots O(N). **Use when.** You need stable references that survive arbitrary deletions (ECS entities, scene graphs, plugin handles, FFI handles). **Language.** Rust `slotmap`, `slab`; C++ entt registry; Java weak handle maps approximate it. **Traps.** Iterating with many holes is wasteful — use a separate dense vector of (slot_key) when iteration is hot.

---

## Linked structures

### Singly linked list

**Invariants.** Each node holds `value` + `next`; tail `next == null`. **Ops.** Push/pop head O(1); arbitrary access O(n); reverse O(n) in place. **Use when.** Freelist, intrusive O(1) splicing, lock-free Treiber stack. **Avoid when.** You want cache locality or random access (almost always). **Traps.** GC languages: easy to leak when nodes outlive the logical list. Most "I want a linked list" instincts are wrong — measure vs. `Vec`.

### Doubly linked list

**Invariants.** `node.prev.next == node && node.next.prev == node`. **Ops.** Splice / erase given an iterator O(1). **Use when.** LRU cache (paired with a hashmap), undo/redo stacks, in-place ordering where mid-erase is hot. **Language.** C++ `std::list`; Java `LinkedList` (rarely the right answer); Rust `LinkedList` (almost never the right answer — `VecDeque` is usually better). **Traps.** Two pointers per node × atomic ref count in some languages = 24-32 bytes overhead per element. Iteration is a *pointer chase*: dominated by cache misses.

### Skip list

**Invariants.** Lane `i+1` is a probabilistic subset (p ≈ 1/2 or 1/4) of lane `i`; sorted within each lane. Expected height O(log n). **Ops.** Search / insert / delete O(log n) expected, O(n) worst. **Use when.** Concurrent ordered map (Redis sorted sets, LevelDB MemTable, Java `ConcurrentSkipListMap`) — easier to make lock-free than balanced trees. **Avoid when.** Single-threaded; B-tree or red-black wins on constants. **Traps.** Choose level cap = ⌈log₂ N_max⌉ + a few; RNG quality matters less than people assume.

### Intrusive list

**Invariants.** Nodes embed the list pointers; container owns nothing. **Use when.** No-allocation hot paths (kernels, embedded), policy where the same object lives in multiple lists. **Language.** Rust `intrusive-collections`; C++ `boost::intrusive`; Linux kernel `list_head`. **Traps.** Lifetimes are manual; mis-managed unlinks are use-after-free landmines.

---

## Balanced search trees (in-memory)

> Rule of thumb: an in-memory ordered map of < 10⁵ entries on modern hardware is faster with `B-tree map` (cache-aware) than with red-black or AVL. Both Rust and Java have a B-tree in stdlib (`BTreeMap` / `TreeMap` — Java's TreeMap is RB but you rarely beat HashMap unless ordering matters).

### Binary search tree (BST, unbalanced)

**Invariants.** For every node: `left.key < node.key < right.key`. **Ops.** Search / insert / delete: O(log n) average for random insertion, O(n) adversarial (sorted insert → chain). **Use when.** Teaching, or as a base for a *balanced* variant. **Production reality.** Almost never the answer. If you need ordered, use a balanced variant or a B-tree.

### AVL tree

**Invariants.** Height-balanced: `|height(left) - height(right)| ≤ 1` at every node. **Ops.** Search / insert / delete O(log n) worst-case; tighter balance than RB → faster lookups, slower updates. **Use when.** Lookup-dominated workloads needing strict height bounds. Memory-constrained ordered maps where rebalance cost is acceptable. **Traps.** Up to 2 rotations per insert, O(log n) on delete; more rotations than RB on average.

### Red-black tree

**Invariants.** Every node red or black; root black; red nodes have black children; every path from root to null has the same number of black nodes. Bound: longest path ≤ 2× shortest. **Ops.** Search / insert / delete O(log n) worst-case. **Use when.** Standard ordered map in many runtimes — `std::map`, Java `TreeMap`, Linux kernel CFS / EPT / VMA, Boehm GC. **Traps.** Looser balance than AVL → slightly slower lookups, fewer rotations per write. *Cache-unfriendly*: each node is a separate allocation, pointer chase per step.

### Treap

**Invariants.** BST on keys; max-heap on randomly assigned priorities. **Ops.** Expected O(log n) with great constants; easy split / merge for ordered statistics. Probabilistic — no worst-case bound. **Use when.** You need split / merge on ordered ranges in one O(log n) op (segment-style rebalancing, persistent variants, competitive programming). **Traps.** RNG quality matters; seeded RNG = adversarial worst case.

### Splay tree

**Invariants.** No height invariant. Every access splays the touched node to the root. **Ops.** Amortized O(log n); worst-case O(n) per op (amortizes out over a sequence). **Use when.** Access pattern is highly skewed (recently used dominates) and you can tolerate variable latency. Memory allocator free lists, some caches. **Avoid when.** Real-time / hard latency budgets. Concurrent: splaying mutates on read, awful for read concurrency.

### Scapegoat tree

**Invariants.** Weight-balanced; on imbalance, rebuild the offending subtree from scratch. **Use when.** Want amortized O(log n) without rotation bookkeeping (no parent pointers / color bits). Persistent variants are clean. **Traps.** Worst-case insert is O(n); pick rebuild α (typically 2/3 or 0.7) deliberately.

### B-tree map (in-memory, cache-aware)

**Invariants.** Node holds up to `2t-1` keys (typical t = 6..12 → 11..23 keys per node); leaves at same depth. **Ops.** Search / insert / delete O(log_b n) — but b ≈ cache-line-fitting fan-out, so 3–6 cache misses for typical N vs ~30+ for RB. **Use when.** Default for in-memory ordered maps when you control the impl. Rust `BTreeMap`, Java `BTreeMap` (Eclipse Collections), CockroachDB internal indexes. **Traps.** Linear scan within a node is fast because of cache locality — don't binary-search a 23-key node; the branch mispredicts dominate.

---

## Range trees

### Fenwick tree (Binary Indexed Tree)

**Invariants.** `tree[i]` stores partial sums over a range determined by `i & -i` (lowbit). **Ops.** Point update + prefix query: O(log n) each. Range-update + point-query via difference trick: O(log n). **Use when.** Frequency counts, prefix sums under updates, inversion counting. Smallest fast range structure (one array of size n). **Avoid when.** Aggregate isn't invertible (min/max, gcd) — use a segment tree. **Traps.** 1-indexed conventionally; off-by-ones bite hard. 2D extension is straightforward but blows up to O(n m log n log m) per query.

### Segment tree

**Invariants.** Each internal node stores the aggregate of its children. **Ops.** Point or range update + range query: O(log n) each. With lazy propagation, range update + range query both O(log n). **Use when.** Non-invertible aggregates (min/max/gcd/xor/affine), range assign, range add + range sum, anything where lazy propagation pays off. **Variants.** Iterative (4× memory, very fast constants), recursive with lazy (cleaner code), Li Chao (CHT-style), persistent (versioning). **Traps.** Size = 4n is the safe bet; some iterative variants need next power-of-two padding. Lazy push-down ordering is the #1 source of bugs.

### Persistent segment tree

**Invariants.** Each update creates O(log n) new nodes; old versions remain reachable. **Ops.** Update / query O(log n); total memory O(n + U log n) for U updates. **Use when.** Versioned range queries (k-th smallest in range [l..r] via persistent BIT/segtree), historical state queries, undo to any prior version. **Traps.** Memory grows linearly with updates; periodically snapshot to a flat array if memory matters.

### Sparse table

**Invariants.** `st[i][j]` stores f(a[j..j + 2^i)) for an *idempotent* f (min, max, gcd, &, |). **Ops.** Build O(n log n); query O(1). **Use when.** Static array, range-min/max queries on huge query volumes. RMQ in LCA pipelines. **Avoid when.** Array is mutable (rebuild is expensive) or aggregate isn't idempotent (sum needs Fenwick instead).

### Wavelet tree

**Invariants.** Recursively partitions values; each level has a bit vector indicating which side each element went. **Ops.** k-th element in range, count of value in range, rank/select on alphabet — all O(log σ) where σ is alphabet size. **Use when.** Compressed text indexes (FM-index), succinct rank/select, 2D point counting via reduction. **Traps.** Implementation-heavy; libraries (sdsl-lite, simdcomp) exist — don't reinvent.

---

## Disk-backed / write-heavy trees

### B-tree (disk, classical)

**Invariants.** Node fan-out matches one disk page (4–64 KiB); leaves at same depth. **Ops.** Read / write a key: O(log_b N) page reads. With B ≈ 100–1000, only 3–4 pages even for billions of keys. **Use when.** Read-heavy OLTP indexes (Postgres, MySQL InnoDB, SQLite default). Single-key point + ordered range scan. **Traps.** Write amplification under update-in-place: a single key change rewrites an entire page. Concurrent updates need page-level latching or MVCC.

### B+ tree

**Invariants.** Same as B-tree but *all values live in leaves*; internal nodes hold only keys; leaves form a linked list. **Ops.** Range scan is linear walk of leaves — no climbing. **Use when.** Range scans matter (almost always for databases). Postgres / MySQL / SQLite / RocksDB all use B+ at the storage layer. **Traps.** Sibling pointer maintenance under concurrent split is subtle — Postgres uses Lehman-Yao with high keys to avoid global latches.

### LSM tree (Log-Structured Merge)

**Invariants.** All writes go to an in-memory MemTable (sorted: skip list or B-tree). When MemTable fills, it's flushed as an immutable sorted run on disk. Background compaction merges overlapping runs. **Ops.** Writes O(1) amortized to MemTable. Reads: check MemTable then progressively older runs (Bloom filter per run avoids most disk reads). **Use when.** Write-heavy workloads, time-series, key-value stores. RocksDB, LevelDB, Cassandra, ScyllaDB, BigTable, HBase. **Traps.** Compaction is *the* operational concern — read amplification, write amplification, space amplification all trade off (RUM conjecture: you can only optimize two of three). Tombstones for deletes pollute reads until compacted away.

### Fractal / B^ε tree

**Invariants.** B-tree where each internal node holds a small in-node buffer of pending operations. **Use when.** Want B+ tree range scans *and* near-LSM write throughput. Tokutek/Percona's TokuDB, Splinterdb. **Traps.** Few production-grade open-source impls; usually not worth building.

### Copy-on-Write B-tree

**Invariants.** Modifications create a new path from root to leaf; old root remains a valid snapshot. **Use when.** Filesystems (btrfs, ZFS, APFS), Postgres index storage (with WAL), any system where snapshots matter. **Traps.** Write amplification proportional to tree depth; needs garbage collection of unreferenced old pages.

---

## Heaps and priority queues

### Binary heap

**Invariants.** Array `h[]` with `h[i] ≤ h[2i+1], h[2i+2]` for min-heap (flip for max). **Ops.** Push O(log n) (sift-up); pop O(log n) (sift-down); peek O(1). Heapify n items O(n) bottom-up. **Use when.** Default priority queue. Top-K via min-heap of size K. **Language.**

- Python: `heapq` — min-heap only. Negate values for max-heap; use tuples `(priority, counter, item)` to break ties deterministically and avoid comparing payloads.
- C++: `std::priority_queue<T>` — max-heap by default; pass `std::greater<T>` for min.
- Rust: `BinaryHeap<T>` — max-heap; wrap with `Reverse(T)` for min.
- Java: `PriorityQueue<T>` — min-heap for natural ordering; pass a `Comparator` to flip.
- Go: `container/heap` — interface-driven; you implement `Less`, `Swap`, `Push`, `Pop`.
- JS: no stdlib heap; use a tiny lib or roll one.

**Traps.** Decrease-key is O(n) because you must find the element first (no index). Pair with a hashmap of value→index for O(log n) decrease-key, *or* use lazy deletion (push duplicates; pop until top is "live").

### d-ary heap

**Invariants.** Each node has up to d children. Push O(log_d n) faster, pop O(d · log_d n) slower. **Use when.** Push-heavy workloads (4-ary is a common sweet spot for Dijkstra on dense graphs).

### Pairing heap

**Invariants.** Lazy merge-based; "amortized analysis is open." **Ops.** Push / merge O(1); decrease-key amortized O(log n) (conjectured O(1)); pop amortized O(log n). **Use when.** Faster than Fibonacci heap in practice for most Dijkstra workloads.

### Fibonacci heap

**Invariants.** Forest of trees; consolidation on extract-min. **Ops.** Push / decrease-key amortized O(1); pop amortized O(log n). **Use when.** Theoretical optimum for Dijkstra / Prim. In practice, *almost never worth the constants* — pairing or quake heaps win on real workloads.

### Indexed priority queue

**Invariants.** Heap + auxiliary `index[key] = heap_position` map. **Ops.** All heap ops + O(log n) decrease-key / change-priority. **Use when.** Dijkstra-on-mutable-graph, event simulation, scheduler queues with priority updates.

### Double-ended priority queue (interval heap, min-max heap)

**Ops.** Get-min / get-max / push / pop-min / pop-max all O(log n). **Use when.** Need both extremes of a stream (running median is better solved with two heaps — see [`algorithms.md`](algorithms.md)).

---

## Hash tables

### Hash functions (pick deliberately)

- **SipHash** — DoS-resistant, used in Python / Rust default. Slower than fast hashes but resists key flood attacks.
- **xxHash / xxh3** — non-cryptographic, ~30 GB/s. Use when keys are trusted.
- **FNV-1a / Murmur3** — older, simpler; xxHash is strictly better in 2024+ except for tiny keys.
- **wyhash / ahash** — fastest options today; default for Rust `ahash`, Go map.
- **CityHash / FarmHash** — Google; CRC-NI-assisted on x86.
- **Cryptographic (BLAKE3 / SHA-256)** — only when collision resistance is part of the threat model.

**Rule:** never use `std::hash<std::string>` for shipping across processes / versions / languages — the seed is process-local on most stdlibs.

### Open addressing (linear probing)

**Invariants.** All entries in the table; collisions resolved by probing successive slots `(h + 1, h + 2, ...) mod cap`. Load factor α < ~0.7–0.85 to keep probe lengths bounded. **Ops.** O(1) average if α is bounded; O(α / (1-α)²) expected probe length. **Use when.** Default for cache-friendly hash tables. C++ `flat_hash_map` (abseil), Rust `HashMap` (since 1.36), Java's record-based maps, Go map (with open chaining variant). **Traps.** Deletes need tombstones or backward-shift; tombstones can pile up — rebuild on too many.

### Robin Hood hashing

**Invariants.** When inserting, if you encounter a slot whose entry probed *less* than you have, swap and continue. Result: bounded probe-length variance. **Use when.** Want predictable worst-case probe distances. Rust `hashbrown` (the standard `HashMap` backend) uses SIMD + Robin Hood.

### Hopscotch hashing

**Invariants.** Each slot has a *neighborhood* (typically 32 slots) within which its real entry must live; lookups touch one cache line. **Use when.** Concurrent-friendly hashing; bounded probe = bounded lock window.

### Cuckoo hashing

**Invariants.** Two (or more) hash functions; each key lives in one of *k* candidate slots; insertion may evict ("kick") another key. **Ops.** Lookup O(1) worst-case (k slots checked); insert amortized O(1), worst-case rebuild. **Use when.** Worst-case O(1) lookup matters (routers, real-time). Bloom-filter alternatives ("cuckoo filters"). **Traps.** Insert can fail and trigger full rebuild — sized for failure rate, not just load.

### Separate chaining

**Invariants.** Each bucket holds a list / dynamic array / tree. **Use when.** Java's `HashMap` since 8 (chains turn into RB trees at chain length 8 to mitigate hash-flood attacks). Easy to implement; deletes are trivial. **Avoid when.** Cache-sensitive code paths — pointer chase per lookup.

### Hash table specialty variants

- **`LinkedHashMap` / insertion-ordered** — Java `LinkedHashMap`, Python `dict` (insertion order since 3.7), JS `Map`, Rust `indexmap::IndexMap`. Use when iteration order or LRU semantics matter.
- **Sorted hash map** — not a thing; if you need both, use a `TreeMap` / `BTreeMap` or pair a hashmap with a heap / linked list.
- **Concurrent hash map** — Java `ConcurrentHashMap` (lock-striped), Rust `DashMap` (sharded), Cliff Click's NonBlockingHashMap (lock-free).

---

## Graphs

### Adjacency list

**Invariants.** `adj[u]` is a list of (v, weight?) tuples. **Use when.** Sparse graphs (most real-world graphs). **Memory.** O(V + E).

### Adjacency matrix

**Invariants.** `adj[u][v]` is edge weight or sentinel. **Use when.** Dense graphs (E ≈ V²), Floyd-Warshall, transitive closure, V ≤ ~5000. **Memory.** O(V²). **Traps.** Iterating neighbors of u is O(V) regardless of degree — bad for sparse traversals.

### CSR (Compressed Sparse Row)

**Invariants.** Two flat arrays: `offsets[V+1]` and `edges[E]`. `adj(u) = edges[offsets[u] .. offsets[u+1]]`. **Use when.** Read-only or batch-rebuild graphs at scale. Numerical sparse matrices. GraphBLAS, SuiteSparse, large-scale BFS on billion-edge graphs. **Traps.** Mutating edges is expensive — rebuild or use a "delta" overlay.

### Edge list

**Invariants.** Just `[(u, v, w), ...]`. **Use when.** Kruskal's MST (sort once by weight), I/O.

### Weighted vs unweighted, directed vs undirected

Track these as types if your language allows — bugs hide in confusing the two. Undirected edges should appear in *both* `adj[u]` and `adj[v]` for an adjacency list.

---

## Tries

### Standard trie

**Invariants.** Children indexed by character; each path from root spells a string. **Ops.** Insert / search / prefix-match O(L) where L is string length, independent of N. **Use when.** Prefix search (autocomplete), longest-common-prefix, dictionaries with small alphabet. **Memory.** Naive impl is profligate (one pointer per character per node). Use array of 26 for English letters, hashmap for arbitrary chars.

### Radix tree / Patricia trie / compressed trie

**Invariants.** Nodes with single children are collapsed into their parents. **Use when.** Memory-tight string indexing. Linux kernel routing table; Postgres `pg_trgm`; many IP routing tables (longest-prefix match). **Traps.** Edge labels are slices — careful with ownership in non-GC languages.

### HAMT (Hash Array Mapped Trie)

**Invariants.** Each node is an array of up to 32 children indexed by 5 bits of the hash; bitmap indicates present slots. **Ops.** Search / insert / delete O(log₃₂ n) ≈ effectively O(1) for practical n. **Use when.** Persistent / immutable maps with structural sharing — Clojure `PersistentHashMap`, Scala `HashMap`, Haskell `unordered-containers`, Rust `im` crate. **Traps.** Path-copy on update means high allocator pressure; use a transient/builder if doing bulk updates.

### Suffix trie / suffix tree

**Invariants.** Contains every suffix of a text S. **Ops.** Substring search O(|pattern|); count occurrences O(|pattern| + #matches). Build O(|S|) (Ukkonen). **Use when.** Multi-pattern substring queries on a fixed text. Bioinformatics, log search. **Practical alt.** Suffix array + LCP array — 5–10× less memory, similar query speed for most workloads.

### Suffix automaton

**Invariants.** DAG with O(|S|) states accepting exactly the substrings of S. **Use when.** Number of distinct substrings, longest common substring of multiple strings, online pattern queries.

---

## Probabilistic / sketches

### Bloom filter

**Invariants.** Bit array of size m + k hash functions. Insert sets k bits. Lookup checks all k bits; if any is 0, definitely not present; if all 1, *probably* present (false positive rate `(1 - e^(-kn/m))^k`, minimized at k = (m/n) ln 2). **Use when.** "Probably not present, check the slow tier" — RocksDB / Cassandra avoid disk reads with per-SSTable bloom filters; CDN cache lookup; spell-checkers. **Avoid when.** You need deletions (use Counting Bloom or Cuckoo filter); false positives are unacceptable (then this is the wrong tool). **Traps.** Picking m and k requires the expected n; underprovisioned, the false-positive rate is useless.

### Counting Bloom filter

**Invariants.** Each cell is a small counter (typically 4 bits) instead of a bit. **Use when.** Need deletes. Counter overflow is the new failure mode.

### Cuckoo filter

**Invariants.** Cuckoo-hash table of small fingerprints. **Ops.** Lookup / insert / delete with false-positive rate ε using ~⌈log₂(2/ε) / α⌉ bits per item. **Use when.** Need a Bloom-filter-shaped membership test with deletes; better space-efficiency than Bloom for ε < 3%.

### Count-Min Sketch

**Invariants.** `d × w` grid; d hash functions; insert increments d cells. Query returns the minimum of those d cells (always ≥ true count; never less). **Use when.** Approximate frequencies in streams ("which IPs are heavy hitters?"). Memory: O(d · w) independent of stream size. **Combine.** Use with a heap of top-K candidates: every increment, query estimate; insert/update in heap if ≥ heap minimum.

### HyperLogLog

**Invariants.** Hash each element; track the maximum run of leading zeros in each of 2^p buckets; estimate cardinality from harmonic mean. **Ops.** Insert O(1); cardinality estimate at any time; merge two HLLs by max-elementwise. **Use when.** Approximate distinct-count over huge streams. Redis `PFADD`/`PFCOUNT`, Spark `approx_count_distinct`, BigQuery `HLL_COUNT`. **Memory.** ~12 KiB gives ~0.81% standard error at any cardinality.

### t-digest

**Invariants.** Centroids clustered tighter near the tails — quantile estimates are best at p99 / p99.9. **Use when.** Approximate percentiles over streams. APM tools (Datadog, Honeycomb internal).

### MinHash / locality-sensitive hashing

**Use when.** Approximate Jaccard similarity over sets (deduplication, near-duplicate web pages, plagiarism).

### Reservoir sampling

**Algorithm** (Algorithm R / Algorithm L). Uniformly sample k items from a stream of unknown length in O(n) time, O(k) space. See [`algorithms.md`](algorithms.md).

---

## Disjoint-set (union-find)

**Invariants.** Each element has a parent pointer; root represents the set; union by rank (or size) + path compression keeps trees flat. **Ops.** Find / union: O(α(n)) amortized — effectively constant. **Use when.** Kruskal's MST, connectivity in offline graph problems, equivalence classes, percolation, image segmentation, Tarjan's offline LCA. **Variants.** Union by rank vs by size (both work; size slightly easier); path compression vs path splitting / halving. *Both* heuristics: O(α(n)). One only: O(log n). **Traps.** Doesn't support split. For *online* SCC / dynamic connectivity, use link-cut trees or Euler-tour trees.

---

## Persistent / immutable

### HAMT (Hash Array Mapped Trie)

See above. Default for persistent unordered maps.

### Persistent vector (Clojure / Scala-style)

**Invariants.** 32-way trie indexed by 5 bits of the index per level; tail-bias for fast append. **Ops.** Append / index / update: effectively O(1) for practical n. **Use when.** Functional languages, immutable state stores (Redux, Elm-style).

### RRB-tree (Relaxed Radix Balanced)

**Invariants.** Persistent vector with O(log n) split, concat, slice. **Use when.** Need persistent vector *with* fast slice / concat — Scala `Vector`, Clojure `core.rrb-vector`.

### Finger tree

**Invariants.** Spine-balanced tree with O(1) amortized push / pop at both ends; O(log n) split / concat with annotated measures. **Use when.** Persistent deque, priority queue, ordered sequence with multiple aggregate views (Haskell `Data.Sequence`).

### Path-copy persistent trees

Any pointer-based tree (RB, BST, segment) can be made persistent by copying the path on update — O(log n) extra nodes per update.

---

## Concurrent / lock-free

### Treiber stack

**Invariants.** Singly linked list; push CAS-replaces head. **Use when.** Lock-free LIFO under low contention. **Traps.** ABA problem — solve with tagged pointers, hazard pointers, or epoch reclamation.

### Michael-Scott queue

**Invariants.** Lock-free FIFO; separate head and tail pointers; dummy node always present. **Use when.** Multi-producer multi-consumer FIFO. Java `ConcurrentLinkedQueue`, .NET `ConcurrentQueue`.

### Vyukov / MPSC bounded queue

**Use when.** Multi-producer single-consumer with bounded capacity (event loops, log shippers, audio).

### LMAX Disruptor

**Invariants.** Ring buffer with a single producer cursor and per-consumer cursors; cache-line padding (64-128 bytes) eliminates false sharing. **Use when.** Ultra-low-latency MPSC / SPSC pipelines (HFT, trading systems).

### RCU (Read-Copy-Update)

**Invariants.** Readers see a consistent snapshot without locks; writer publishes a new version, defers reclamation until all in-flight readers leave the grace period. **Use when.** Read-mostly concurrent maps / lists. Linux kernel routing tables, dcache.

### Hazard pointers / epoch-based reclamation

**Use when.** Lock-free structures that need safe memory reclamation. Rust `crossbeam-epoch`, C++ `folly::hazptr`.

### Sharded / lock-striped concurrent maps

**Invariants.** N independent submaps, each guarded by its own lock; key.hash → shard. **Use when.** Java `ConcurrentHashMap`, Rust `DashMap`. Cheaper than lock-free for many real workloads.

---

## Spatial

### KD-tree

**Invariants.** BST splitting alternately on each dimension. **Ops.** Nearest neighbor expected O(log n) in low D; degrades toward O(n) at D ≥ ~20 ("curse of dimensionality"). **Use when.** k-NN, range search, ray tracing acceleration in low dimensions.

### R-tree / R*-tree

**Invariants.** Bounding-box hierarchy; minimum bounding rectangle per subtree. **Use when.** Geospatial indexes (PostGIS, SQLite R*Tree, GeoMesa), 2D / 3D collision broadphase.

### Quadtree / Octree

**Use when.** 2D / 3D uniform spatial partitioning (games, image processing, particle systems).

### BVH (Bounding Volume Hierarchy)

**Use when.** Ray tracing, broad-phase collision; better than uniform grid for varied object sizes.

### Z-order curve / Hilbert curve

**Use when.** Reduce multi-D queries to 1D for B-tree indexing (Postgres BRIN, BigTable row keys).

---

## Text-edit specific

### Rope

**Invariants.** Balanced binary tree of string chunks; in-order leaves concatenate to the document. **Ops.** Insert / delete at arbitrary index O(log n); concat O(log n). **Use when.** Large-document text editors (Xi editor, Helix), real-time collaborative documents.

### Gap buffer

**Invariants.** Single contiguous buffer with a "gap" at the cursor; edits move the gap. **Use when.** Single-cursor editors (Emacs). O(1) edits near the cursor; O(n) to move the gap a long way.

### Piece table

**Invariants.** Original immutable buffer + append-only "added" buffer; document is a sequence of `(buffer, offset, length)` pieces. **Use when.** Editors that need very cheap insert (Word, VSCode internally). Undo is easy because the original never changes.

### CRDT structures (for collaborative editing)

**Use when.** Real-time multi-user editing without a central server. Look up: Yjs (Y.Doc), Automerge, Logoot, RGA, LSEQ.
