// Microbench scaffold (Rust / criterion) with the discipline from
// references/verification.md → Microbench discipline.
//
// What this scaffold gets right (so you don't have to remember every time):
//   - Defeats dead-code elimination by `std::hint::black_box`.
//   - Sweeps the access pattern: sequential, random, zipfian.
//   - Sweeps the working-set size to expose cache effects.
//   - Criterion handles warmup, statistical sampling, and IQR / outlier
//     reporting out of the box.
//
// To adapt:
//   1. Replace `MyStructure` with your real impl.
//   2. Adjust `WORKLOAD_SIZES` and `DISTRIBUTIONS` to match what you care about.
//   3. Add benches for the specific operations on your hot path.
//
// Cargo.toml:
//   [dev-dependencies]
//   criterion = { version = "0.5", features = ["html_reports"] }
//   rand = "0.8"
//
//   [[bench]]
//   name = "bench"
//   harness = false
//
// Place this file at `benches/bench.rs`.
//
// Run:
//   cargo bench
//
// Hostile environments — on Linux, before running:
//   sudo cpupower frequency-set -g performance
//   taskset -c 0 nice -n -20 cargo bench

use std::collections::HashMap;
use std::hint::black_box;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use rand::distributions::Distribution as RandDist;
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};
use rand_distr::Zipf;

// ---------------------------------------------------------------------------
// 1. Replace with your real structure.
// ---------------------------------------------------------------------------

pub struct MyStructure {
    items: HashMap<i32, i32>,
}

impl MyStructure {
    pub fn new() -> Self {
        Self {
            items: HashMap::new(),
        }
    }
    pub fn with_capacity(n: usize) -> Self {
        Self {
            items: HashMap::with_capacity(n),
        }
    }
    pub fn insert(&mut self, k: i32, v: i32) {
        self.items.insert(k, v);
    }
    pub fn lookup(&self, k: i32) -> Option<&i32> {
        self.items.get(&k)
    }
    pub fn delete(&mut self, k: i32) {
        self.items.remove(&k);
    }
}

// ---------------------------------------------------------------------------
// 2. Workload generators.
// ---------------------------------------------------------------------------

const WORKLOAD_SIZES: &[usize] = &[1_000, 10_000, 100_000];

#[derive(Copy, Clone, Debug)]
enum Distribution {
    Sequential,
    Random,
    Zipfian,
}

const DISTRIBUTIONS: &[Distribution] = &[
    Distribution::Sequential,
    Distribution::Random,
    Distribution::Zipfian,
];

fn dist_name(d: Distribution) -> &'static str {
    match d {
        Distribution::Sequential => "seq",
        Distribution::Random => "rand",
        Distribution::Zipfian => "zipf",
    }
}

fn gen_keys(n: usize, d: Distribution, seed: u64) -> Vec<i32> {
    let mut rng = StdRng::seed_from_u64(seed);
    let mut out = Vec::with_capacity(n);
    match d {
        Distribution::Sequential => {
            for i in 0..n {
                out.push(i as i32);
            }
        }
        Distribution::Random => {
            let upper = (n * 10) as i32;
            for _ in 0..n {
                out.push(rng.gen_range(0..upper));
            }
        }
        Distribution::Zipfian => {
            // Zipf with alpha=1.5 on N items; map into key space (n*10) to
            // emulate heavy-hitter access onto a larger universe.
            let z = Zipf::new(n as u64, 1.5).expect("valid zipf params");
            let upper = (n * 10) as i32;
            for _ in 0..n {
                let v = z.sample(&mut rng) as i32;
                out.push(v.rem_euclid(upper));
            }
        }
    }
    out
}

fn populate(s: &mut MyStructure, keys: &[i32]) {
    for (i, &k) in keys.iter().enumerate() {
        s.insert(k, i as i32);
    }
}

// ---------------------------------------------------------------------------
// 3. The benches.
// ---------------------------------------------------------------------------

fn bench_insert(c: &mut Criterion) {
    let mut group = c.benchmark_group("insert");
    for &n in WORKLOAD_SIZES {
        for &d in DISTRIBUTIONS {
            let keys = gen_keys(n, d, 0xFACE);
            group.throughput(Throughput::Elements(n as u64));
            group.bench_with_input(
                BenchmarkId::new(format!("dist_{}", dist_name(d)), n),
                &keys,
                |b, keys| {
                    b.iter(|| {
                        let mut s = MyStructure::with_capacity(keys.len());
                        for (i, &k) in keys.iter().enumerate() {
                            s.insert(black_box(k), black_box(i as i32));
                        }
                        black_box(s);
                    });
                },
            );
        }
    }
    group.finish();
}

fn bench_lookup(c: &mut Criterion) {
    let mut group = c.benchmark_group("lookup");
    for &n in WORKLOAD_SIZES {
        for &d in DISTRIBUTIONS {
            // Populate from the chosen distribution.
            let insert_keys = gen_keys(n, d, 0xFACE);
            let mut s = MyStructure::with_capacity(n);
            populate(&mut s, &insert_keys);

            // Always query from a random pattern (the realistic shape).
            let query_keys = gen_keys(n, Distribution::Random, 0xBEEF);

            group.throughput(Throughput::Elements(n as u64));
            group.bench_with_input(
                BenchmarkId::new(format!("dist_{}", dist_name(d)), n),
                &query_keys,
                |b, query_keys| {
                    b.iter(|| {
                        let mut acc = 0i32;
                        for &k in query_keys.iter() {
                            if let Some(&v) = s.lookup(black_box(k)) {
                                acc ^= v;
                            }
                        }
                        black_box(acc)
                    });
                },
            );
        }
    }
    group.finish();
}

fn bench_mixed(c: &mut Criterion) {
    let mut group = c.benchmark_group("mixed_80r_15w_5d");
    for &n in WORKLOAD_SIZES {
        for &d in DISTRIBUTIONS {
            let insert_keys = gen_keys(n, d, 0xFACE);
            let ops_keys = gen_keys(n, Distribution::Random, 0xDEAD);
            let mut rng = StdRng::seed_from_u64(0xBEEF);
            let rolls: Vec<f32> = (0..n).map(|_| rng.gen::<f32>()).collect();

            group.throughput(Throughput::Elements(n as u64));
            group.bench_with_input(
                BenchmarkId::new(format!("dist_{}", dist_name(d)), n),
                &(insert_keys.clone(), ops_keys.clone(), rolls.clone()),
                |b, (insert_keys, ops_keys, rolls)| {
                    b.iter(|| {
                        let mut s = MyStructure::with_capacity(insert_keys.len());
                        populate(&mut s, insert_keys);
                        let mut acc = 0i32;
                        for (i, &k) in ops_keys.iter().enumerate() {
                            let r = rolls[i];
                            if r < 0.80 {
                                if let Some(&v) = s.lookup(black_box(k)) {
                                    acc ^= v;
                                }
                            } else if r < 0.95 {
                                s.insert(black_box(k), 1);
                            } else {
                                s.delete(black_box(k));
                            }
                        }
                        black_box(acc)
                    });
                },
            );
        }
    }
    group.finish();
}

criterion_group!(benches, bench_insert, bench_lookup, bench_mixed);
criterion_main!(benches);

// NOTE on reporting (see references/verification.md → Bench reporting template):
//   ALWAYS report the environment alongside the numbers:
//     - CPU model and core pinning
//     - RAM, kernel, libc, allocator (try jemallocator / mimalloc-rust)
//     - rustc version, profile flags
//     - any frequency-governor / turbo settings
//   Criterion writes HTML reports to `target/criterion/`; include the env
//   block in commit messages or in the PR body so future-you can diff them.
