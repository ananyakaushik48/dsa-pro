# Verification

How to actually convince yourself a non-trivial structure works, and how to know it's fast.

## Three checkpoints

1. **Invariant checks.** Encode the structure's defining property as a function `check_invariants(s) -> bool`. Call it after *every* mutation in property tests and fuzz harnesses. If your structure can't easily express its invariants, you don't fully understand it yet.
2. **Oracle comparison.** Implement (or use) a trivially correct reference (a sorted array, a hashmap, a brute-force loop) and test that *every sequence of operations* produces identical observable behavior. This is the single highest-value test you can write for a custom data structure.
3. **Microbenchmarks in the prod-shaped environment.** Big-O reasoning sets the lower bound; constants determine whether you ship. Same structure, same algorithm, 10× faster or slower depending on key distribution, working-set size, JIT/allocator/CPU.

## Invariants by family

| Family | Invariant |
|--------|-----------|
| BST | `for every node: max(left subtree) < node.key < min(right subtree)` |
| AVL | `\|height(left) - height(right)\| ≤ 1` at every node; height correct |
| Red-black | Root black; red has only black children; every root→null path has the same black height |
| Min-heap | `h[i] ≤ h[2i+1] && h[i] ≤ h[2i+2]` for all valid i; size matches |
| Hash table | Load factor ≤ configured max; for every (k, v) — `lookup(k) == Some(v)`; for k not inserted — `lookup(k) == None`; no tombstone count exceeds threshold |
| B-tree | Leaves at same depth; node key count in [t-1, 2t-1] except root; keys per node sorted |
| LSM | Each level non-overlapping (in leveled compaction); MemTable ≤ flush threshold; level sizes monotone non-decreasing |
| Segment tree | Aggregate at internal node = combine(left.agg, right.agg); lazy clean after push-down |
| Fenwick | After `update(i, d)`, `query(i) - query(i-1)` reflects the cumulative delta |
| DSU | Path from any node to its root is well-defined; rank/size at root is correct; `find(find(x)) == find(x)` |
| Trie | Every leaf (or marked node) represents an inserted key; path from root spells exactly that key |
| Bloom filter | After insert(k), `contains(k) == true`; FPR over a random sample ≤ target FPR within statistical bounds |
| HyperLogLog | After bulk insert of n distinct elements, `\|estimate - n\| / n ≤ ~1.04 / √(2^p)` 65% of the time |
| Persistent vector | After `update(v, i, x)`, original v is unchanged and `get(v, i) != x`; new version `get(v', i) == x` |
| Lock-free queue | Linearizable: every operation has a single linearization point; FIFO order preserved across enqueue / dequeue pairs |

## Property test patterns

### The oracle pattern (the single most useful test)

```text
@property
def test_oracle(ops: List[Op]):
  custom = MyStructure()
  oracle = ReferenceImpl()   # e.g., sorted list, dict, whatever's obviously correct
  for op in ops:
    apply op to both
    assert observable_state(custom) == observable_state(oracle)
    assert custom.check_invariants()
```

- Generate ops at random — `(Insert k v) | (Delete k) | (Lookup k) | (Iterate)`.
- Shrinker must shrink the *op sequence*, not individual fields, to find minimal counterexamples.
- Property tests catch interaction bugs (e.g., "delete after rehash with this specific load factor"); unit tests miss them.

### Invariant-after-every-op

```text
@property
def test_invariants_hold(ops):
  s = MyStructure()
  for op in ops:
    s.apply(op)
    assert s.check_invariants(), f"after {op}, invariants broken"
```

### Round-trip / inverse

```text
@property
def test_insert_delete_roundtrip(items):
  s = MyStructure()
  for k in items: s.insert(k)
  for k in items: assert k in s
  for k in items: s.delete(k)
  assert s.is_empty()
```

### Equivalence under reordering

```text
@property
def test_set_semantics(items):
  for perm in permutations(items, sample=10):
    s = MyStructure()
    for k in perm: s.insert(k)
    assert sorted(s.iter()) == sorted(items_dedup)
```

### Stress with shrinking

When a test fails, the framework shrinks the operation sequence to a minimal counterexample. Always preserve enough state to print: input sequence + final state + which invariant was violated.

## Frameworks per language

| Language | Property | Microbench | Fuzzer |
|----------|----------|------------|--------|
| TypeScript / JS | `fast-check` | `tinybench`, `mitata` | `jazzer.js`, `@jsfuzz/core` |
| Python | `hypothesis` | `pytest-benchmark`, `asv` | `atheris`, `python-afl` |
| Rust | `proptest`, `quickcheck` | `criterion`, `divan` | `cargo-fuzz`, `afl.rs` |
| Java / JVM | `jqwik`, `junit-quickcheck` | `JMH` | `jazzer` |
| C++ | `rapidcheck` | Google Benchmark, `nanobench` | `libFuzzer`, AFL++ |
| Go | `testing/quick`, `gopter` | `testing.B`, `benchstat` | `go test -fuzz` |

See drop-in scaffolds: `scripts/proptest.{ts,py,rs}`, `scripts/bench.{ts,py,rs}`.

## Differential / oracle testing

When two implementations claim equivalence (your fast custom code vs. a trusted baseline, or two ports of the same algorithm), feed them the same random inputs and compare:

```text
generate input (small enough that the reference finishes)
run candidate, run oracle
assert candidate.result == oracle.result
```

Beyond random:
- **Mutation-guided differential fuzzing** (libFuzzer style) — coverage-guided generation finds inputs that exercise new code paths.
- **Structure-aware fuzzing** — generate valid op sequences (not random bytes) for richer coverage.

## Concurrency testing

- **`loom` (Rust) / `Helgrind` (C) / `TSan`** — exhaustively explore thread interleavings.
- **`shuttle` (Rust)** — randomized interleaving with controllable seed (faster than loom; lower coverage).
- **JCStress (Java)** — concurrency invariant tester.
- **For lock-free structures, you *must* test under both `TSan` and `loom`-style exhaustive interleaving.** Single-threaded property tests miss the entire failure mode.

## Microbench discipline

Common pitfalls (in order of how badly they wreck your numbers):

1. **Dead code elimination.** Compiler / JIT decides your benchmark loop has no observable effect → measures nothing. Use `std::hint::black_box` (Rust), `Blackhole.consume` (JMH), `noinline` + global volatile sink, or print the accumulated value.
2. **No warmup.** JIT compilers (HotSpot, V8, .NET) profile-guide-optimize a hot loop after thousands of iterations. Measure *only* after warmup: `criterion`, `JMH`, `tinybench` handle this.
3. **CPU frequency scaling.** Modern CPUs throttle / boost dynamically. Pin to performance governor on Linux (`cpupower frequency-set -g performance`), disable turbo, run as a single thread on a pinned core.
4. **Statistical sloppiness.** Report median + IQR or 95% CI, not "best of 3" or single runs. `criterion` and `tinybench` plot distributions for you.
5. **Working-set inversion.** Allocating once and reusing the buffer hits L1; the realistic workload re-allocates and hits DRAM. Match the bench's allocation pattern to prod.
6. **Single distribution.** Hash tables are 10× faster on dense integer keys than on random strings. Bench at least: (a) sequential, (b) random, (c) zipfian / power-law.
7. **OS noise.** Run with `--isolate`, on a quiet machine, with `nice -n -20`. Multiple runs; reject runs with high variance.

## Bench reporting template

A bench report is useless without context. Always include:

```text
Structure:  <name and config (capacity, load factor, key type)>
Workload:   <op mix, key distribution, value size, N>
Environment: <CPU, cores, RAM, kernel, libc, allocator, language/runtime version>
Counters:   median, p99, IQR or CI95 from <num_samples>; cache misses (perf), branch misses, IPC (where measurable)
```

Without these, "twice as fast" means nothing.

## Allocator awareness

- **Default allocator behavior matters more than people admit.** Glibc malloc, jemalloc, mimalloc, mimalloc-secure, snmalloc, scudo all have different behavior under fragmentation and concurrent allocation. Try `MALLOC_CONF` (jemalloc), `LD_PRELOAD=libmimalloc.so`, or compile against an alternate allocator.
- **Per-thread arenas** drastically improve concurrent alloc; jemalloc and tcmalloc have them by default.
- **Bump allocators / arenas / pools** beat the system allocator when lifetimes are bulk (per request, per frame, per simulation step) — `bumpalo` (Rust), `std::pmr::monotonic_buffer_resource` (C++17), Arena allocator (Go via `sync.Pool` for object recycling).
- **Avoid `realloc` in hot paths.** Preallocate; or grow with the structure's documented strategy and tolerate one-time cost.

## When to stop optimizing

- The bench is **flat at the cache line.** A `Vec` linear scan at memory bandwidth (10–50 GB/s) is the asymptote.
- The hot loop **retires ≥ 3 instructions per cycle** on modern x86 / ARM (use `perf stat -e cycles,instructions`).
- Branch mispredict rate **< 1%** on the hot loop.
- Cache miss rate **bounded** by working set / cache size.
- Allocations per op **= 0** in the steady state.

If you're past those, more cleverness will likely make the code worse without measurable wins.
