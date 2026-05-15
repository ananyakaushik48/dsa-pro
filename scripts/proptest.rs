//! Property-test scaffold (Rust + proptest).
//!
//! Cargo.toml:
//!   [dev-dependencies]
//!   proptest = "1"
//!
//! Run: cargo test --release --test proptest
//!
//! Pattern: oracle comparison + invariant check after every op.
//! Adapt `MyStructure`, `OracleImpl`, and `Op`.

use proptest::prelude::*;
use std::collections::HashMap;

// ─── (1) Replace with the candidate ───
#[derive(Default)]
struct MyStructure<V> {
    data: HashMap<i64, V>,
}

impl<V: Clone + PartialEq> MyStructure<V> {
    fn insert(&mut self, k: i64, v: V) {
        self.data.insert(k, v);
    }
    fn delete(&mut self, k: i64) -> bool {
        self.data.remove(&k).is_some()
    }
    fn lookup(&self, k: i64) -> Option<&V> {
        self.data.get(&k)
    }
    fn size(&self) -> usize {
        self.data.len()
    }

    /// Encode the structure's defining invariant(s). Return false on violation.
    fn check_invariants(&self) -> bool {
        // e.g., for BST: in-order traversal is strictly sorted
        // for heap: every parent <= children
        // for hash table: load factor <= configured max; all inserted keys retrievable
        true
    }
}

// ─── (2) Reference: trivially correct, slow is fine ───
#[derive(Default)]
struct OracleImpl<V> {
    data: Vec<(i64, V)>,
}

impl<V: Clone + PartialEq> OracleImpl<V> {
    fn insert(&mut self, k: i64, v: V) {
        if let Some(slot) = self.data.iter_mut().find(|(kk, _)| *kk == k) {
            slot.1 = v;
        } else {
            self.data.push((k, v));
        }
    }
    fn delete(&mut self, k: i64) -> bool {
        if let Some(pos) = self.data.iter().position(|(kk, _)| *kk == k) {
            self.data.remove(pos);
            true
        } else {
            false
        }
    }
    fn lookup(&self, k: i64) -> Option<&V> {
        self.data.iter().find(|(kk, _)| *kk == k).map(|(_, v)| v)
    }
    fn size(&self) -> usize {
        self.data.len()
    }
}

// ─── (3) Operations the property test will generate ───
#[derive(Clone, Debug)]
enum Op {
    Insert(i64, i64),
    Delete(i64),
    Lookup(i64),
}

fn op_strategy() -> impl Strategy<Value = Op> {
    prop_oneof![
        (any::<i64>(), any::<i64>()).prop_map(|(k, v)| Op::Insert(k, v)),
        any::<i64>().prop_map(Op::Delete),
        any::<i64>().prop_map(Op::Lookup),
    ]
}

fn apply_and_compare(
    op: &Op,
    candidate: &mut MyStructure<i64>,
    oracle: &mut OracleImpl<i64>,
) -> Result<(), TestCaseError> {
    match op {
        Op::Insert(k, v) => {
            candidate.insert(*k, *v);
            oracle.insert(*k, *v);
        }
        Op::Delete(k) => {
            let a = candidate.delete(*k);
            let b = oracle.delete(*k);
            prop_assert_eq!(a, b, "delete({}) disagreed", k);
        }
        Op::Lookup(k) => {
            let a = candidate.lookup(*k).copied();
            let b = oracle.lookup(*k).copied();
            prop_assert_eq!(a, b, "lookup({}) disagreed", k);
        }
    }
    prop_assert_eq!(candidate.size(), oracle.size());
    prop_assert!(candidate.check_invariants(), "invariants broken after {:?}", op);
    Ok(())
}

proptest! {
    #![proptest_config(ProptestConfig {
        cases: 500,
        max_shrink_iters: 1_000,
        .. ProptestConfig::default()
    })]

    /// Random op sequences must produce identical observable behavior.
    #[test]
    fn ops_match_oracle(ops in prop::collection::vec(op_strategy(), 0..200)) {
        let mut candidate = MyStructure::default();
        let mut oracle = OracleImpl::default();
        for op in &ops {
            apply_and_compare(op, &mut candidate, &mut oracle)?;
        }
    }

    /// Insert-then-delete in any permutation leaves structure empty.
    #[test]
    fn insert_delete_roundtrip(keys in prop::collection::vec(any::<i64>(), 0..200)) {
        let mut s: MyStructure<i64> = MyStructure::default();
        let unique: std::collections::HashSet<i64> = keys.iter().copied().collect();
        for &k in &unique { s.insert(k, k); }
        for &k in &unique { s.delete(k); }
        prop_assert_eq!(s.size(), 0);
        prop_assert!(s.check_invariants());
    }
}
