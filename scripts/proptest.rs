// Property-test scaffold (Rust / proptest) using the oracle pattern.
//
// The oracle pattern is the single highest-value test for a custom data
// structure (see references/verification.md). Generate a random sequence of
// operations, apply it to both your custom structure and a trivially correct
// reference (the "oracle"), and assert that observable behavior matches after
// every op.
//
// To adapt:
//   1. Replace `MyStructure` and `Oracle` with your real types.
//   2. Edit the `Op` enum + the strategy to match your API.
//   3. Implement `apply_op` for both sides.
//   4. Implement `observable_state` so the assert compares everything the caller can see.
//   5. Implement `check_invariants` to encode the structure's defining property.
//
// Cargo.toml:
//   [dev-dependencies]
//   proptest = "1.4"
//
// Run:
//   cargo test --test proptest -- --nocapture
//
// (Place this file at `tests/proptest.rs` or run as a regular test module
// inside `src/` with `#[cfg(test)] mod proptest { ... }`.)

use std::collections::BTreeMap;

use proptest::collection::vec;
use proptest::prelude::*;

// ---------------------------------------------------------------------------
// 1. Replace these with your real types.
// ---------------------------------------------------------------------------

#[derive(Default, Debug, Clone)]
pub struct MyStructure {
    items: BTreeMap<i32, String>,
}

impl MyStructure {
    pub fn new() -> Self {
        Self::default()
    }
    pub fn insert(&mut self, k: i32, v: String) {
        self.items.insert(k, v);
    }
    pub fn delete(&mut self, k: i32) {
        self.items.remove(&k);
    }
    pub fn lookup(&self, k: i32) -> Option<&String> {
        self.items.get(&k)
    }
    pub fn iter_sorted(&self) -> Vec<(i32, String)> {
        self.items.iter().map(|(k, v)| (*k, v.clone())).collect()
    }
    pub fn check_invariants(&self) -> bool {
        // Encode the structure's defining property here. For a real custom
        // impl this might be balance, load-factor bounds, etc.
        // BTreeMap already guarantees ordering — placeholder check:
        let keys: Vec<_> = self.items.keys().copied().collect();
        keys.windows(2).all(|w| w[0] < w[1])
    }
}

#[derive(Default, Debug, Clone)]
pub struct Oracle {
    items: BTreeMap<i32, String>,
}

impl Oracle {
    pub fn new() -> Self {
        Self::default()
    }
    pub fn insert(&mut self, k: i32, v: String) {
        self.items.insert(k, v);
    }
    pub fn delete(&mut self, k: i32) {
        self.items.remove(&k);
    }
    pub fn lookup(&self, k: i32) -> Option<&String> {
        self.items.get(&k)
    }
    pub fn iter_sorted(&self) -> Vec<(i32, String)> {
        self.items.iter().map(|(k, v)| (*k, v.clone())).collect()
    }
}

// ---------------------------------------------------------------------------
// 2. Op model. Edit to match your API.
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub enum Op {
    Insert(i32, String),
    Delete(i32),
    Lookup(i32),
    Iter,
}

#[derive(Debug, PartialEq, Eq)]
pub enum ObservableResult {
    None,
    Lookup(Option<String>),
    Iter(Vec<(i32, String)>),
}

fn op_strategy() -> impl Strategy<Value = Op> {
    prop_oneof![
        (-100i32..=100, ".{0,8}").prop_map(|(k, v)| Op::Insert(k, v)),
        (-100i32..=100).prop_map(Op::Delete),
        (-100i32..=100).prop_map(Op::Lookup),
        Just(Op::Iter),
    ]
}

// ---------------------------------------------------------------------------
// 3. Apply + observe.
// ---------------------------------------------------------------------------

fn apply_op_custom(s: &mut MyStructure, op: &Op) -> ObservableResult {
    match op {
        Op::Insert(k, v) => {
            s.insert(*k, v.clone());
            ObservableResult::None
        }
        Op::Delete(k) => {
            s.delete(*k);
            ObservableResult::None
        }
        Op::Lookup(k) => ObservableResult::Lookup(s.lookup(*k).cloned()),
        Op::Iter => ObservableResult::Iter(s.iter_sorted()),
    }
}

fn apply_op_oracle(s: &mut Oracle, op: &Op) -> ObservableResult {
    match op {
        Op::Insert(k, v) => {
            s.insert(*k, v.clone());
            ObservableResult::None
        }
        Op::Delete(k) => {
            s.delete(*k);
            ObservableResult::None
        }
        Op::Lookup(k) => ObservableResult::Lookup(s.lookup(*k).cloned()),
        Op::Iter => ObservableResult::Iter(s.iter_sorted()),
    }
}

fn observable_state(s: &MyStructure) -> Vec<(i32, String)> {
    s.iter_sorted()
}

// ---------------------------------------------------------------------------
// 4. The actual property tests.
// ---------------------------------------------------------------------------

proptest! {
    #![proptest_config(ProptestConfig {
        cases: 256,
        max_shrink_iters: 10_000,
        .. ProptestConfig::default()
    })]

    /// Oracle pattern: for every op sequence, observable behavior matches the
    /// oracle and invariants hold after every step.
    #[test]
    fn oracle_matches(ops in vec(op_strategy(), 0..200)) {
        let mut custom = MyStructure::new();
        let mut oracle = Oracle::new();
        for op in &ops {
            let r_custom = apply_op_custom(&mut custom, op);
            let r_oracle = apply_op_oracle(&mut oracle, op);
            prop_assert_eq!(&r_custom, &r_oracle,
                "op {:?} produced {:?} on custom but {:?} on oracle", op, r_custom, r_oracle);
            prop_assert!(custom.check_invariants(),
                "invariants violated after op {:?}; state {:?}", op, observable_state(&custom));
        }
        prop_assert_eq!(observable_state(&custom), oracle.iter_sorted());
    }

    /// Invariants hold after every op even without comparing to an oracle.
    #[test]
    fn invariants_hold(ops in vec(op_strategy(), 0..200)) {
        let mut s = MyStructure::new();
        for op in &ops {
            apply_op_custom(&mut s, op);
            prop_assert!(s.check_invariants(),
                "invariants violated after op {:?}", op);
        }
    }

    /// Every key inserted is findable; deleting all keys clears them all.
    #[test]
    fn insert_delete_roundtrip(items in vec((any::<i32>(), ".{0,8}"), 0..200)) {
        let mut s = MyStructure::new();
        let mut dedup: BTreeMap<i32, String> = BTreeMap::new();
        for (k, v) in &items {
            s.insert(*k, v.clone());
            dedup.insert(*k, v.clone());
        }
        for (k, v) in &dedup {
            prop_assert_eq!(s.lookup(*k), Some(v));
        }
        for k in dedup.keys() {
            s.delete(*k);
        }
        for k in dedup.keys() {
            prop_assert_eq!(s.lookup(*k), None);
        }
    }
}

// ---------------------------------------------------------------------------
// 5. Concurrency stress.
//
// For lock-free / concurrent structures, single-threaded property tests miss
// the entire failure mode. Pair this scaffold with `loom` or `shuttle` to
// exhaustively explore interleavings. Example skeleton:
//
//   #[cfg(loom)]
//   #[test]
//   fn lockfree_linearizable() {
//       loom::model(|| {
//           let s = std::sync::Arc::new(MyLockFreeStructure::new());
//           let s2 = s.clone();
//           let t1 = loom::thread::spawn(move || s.insert(1, "a".into()));
//           let t2 = loom::thread::spawn(move || { let _ = s2.lookup(1); });
//           t1.join().unwrap();
//           t2.join().unwrap();
//           assert!(s.check_invariants());
//       });
//   }
