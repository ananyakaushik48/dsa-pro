//! Microbench scaffold (Rust + criterion).
//!
//! Cargo.toml:
//!   [dev-dependencies]
//!   criterion = { version = "0.5", features = ["html_reports"] }
//!   rand = "0.8"
//!   rand_distr = "0.4"
//!
//!   [[bench]]
//!   name = "bench"
//!   harness = false
//!
//! Run: cargo bench --bench bench -- --warm-up-time 2 --measurement-time 5
//!
//! Disciplines applied:
//!   - Distribution sweep: sequential / random / zipfian
//!   - Working-set sweep: tiny / fits-L2 / spills to DRAM
//!   - `black_box` to defeat DCE
//!   - Criterion reports median + bootstrapped CI

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use rand::prelude::*;
use rand_distr::{Distribution, Zipf};
use std::collections::HashMap;

fn seq_keys(n: usize) -> Vec<u64> {
    (0..n as u64).collect()
}

fn random_keys(n: usize) -> Vec<u64> {
    let mut rng = StdRng::seed_from_u64(0xC0FFEE);
    (0..n).map(|_| rng.gen()).collect()
}

fn zipfian_keys(n: usize, alpha: f64) -> Vec<u64> {
    let mut rng = StdRng::seed_from_u64(0xBEEF);
    let z = Zipf::new(n as u64, alpha).unwrap();
    (0..n).map(|_| z.sample(&mut rng) as u64).collect()
}

const WORKING_SETS: &[(&str, usize)] = &[
    ("4K-L1ish", 4_000),
    ("64K-L2ish", 64_000),
    ("1M-DRAM", 1_000_000),
];

fn bench_hash_insert(c: &mut Criterion) {
    let mut g = c.benchmark_group("hashmap-insert");
    for (ws_name, n) in WORKING_SETS {
        for (dist_name, ks) in [
            ("seq", seq_keys(*n)),
            ("rand", random_keys(*n)),
            ("zipf", zipfian_keys(*n, 1.1)),
        ] {
            g.throughput(Throughput::Elements(*n as u64));
            g.bench_with_input(
                BenchmarkId::new(*ws_name, dist_name),
                &ks,
                |b, ks| {
                    b.iter(|| {
                        let mut m: HashMap<u64, u64> = HashMap::with_capacity(ks.len());
                        for (i, k) in ks.iter().enumerate() {
                            m.insert(*k, i as u64);
                        }
                        black_box(m.len())
                    })
                },
            );
        }
    }
    g.finish();
}

fn bench_hash_lookup(c: &mut Criterion) {
    let mut g = c.benchmark_group("hashmap-lookup");
    for (ws_name, n) in WORKING_SETS {
        for (dist_name, ks) in [
            ("seq", seq_keys(*n)),
            ("rand", random_keys(*n)),
            ("zipf", zipfian_keys(*n, 1.1)),
        ] {
            let built: HashMap<u64, u64> = ks.iter().enumerate().map(|(i, k)| (*k, i as u64)).collect();
            g.throughput(Throughput::Elements(*n as u64));
            g.bench_with_input(
                BenchmarkId::new(*ws_name, dist_name),
                &(ks.clone(), built),
                |b, (ks, built)| {
                    b.iter(|| {
                        let mut acc = 0u64;
                        for k in ks {
                            acc = acc.wrapping_add(*built.get(k).unwrap_or(&0));
                        }
                        black_box(acc)
                    })
                },
            );
        }
    }
    g.finish();
}

criterion_group!(benches, bench_hash_insert, bench_hash_lookup);
criterion_main!(benches);
