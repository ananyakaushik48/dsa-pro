"""
Property-test scaffold (Python + Hypothesis).

Install: pip install hypothesis pytest
Run:     pytest proptest.py -q

Pattern: oracle comparison + invariant check after every op.
Adapt `MyStructure`, `OracleImpl`, the `Bundle`/`Rule` machinery for stateful testing.
"""

from typing import Any
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, precondition


# ─── (1) Replace with the candidate ───
class MyStructure:
    def __init__(self) -> None:
        self._data: dict[int, Any] = {}

    def insert(self, k: int, v: Any) -> None:
        self._data[k] = v

    def delete(self, k: int) -> bool:
        return self._data.pop(k, None) is not None

    def lookup(self, k: int) -> Any:
        return self._data.get(k)

    def __len__(self) -> int:
        return len(self._data)

    def check_invariants(self) -> bool:
        """Encode the structure's defining invariant(s). Return False on violation."""
        # e.g., for BST: in-order traversal is strictly sorted
        # for heap: every parent ≤ children
        # for hash table: load factor ≤ configured max; all inserted keys retrievable
        return True


# ─── (2) Reference: trivially correct, slow is fine ───
class OracleImpl:
    def __init__(self) -> None:
        self._data: list[tuple[int, Any]] = []

    def insert(self, k: int, v: Any) -> None:
        for i, (kk, _) in enumerate(self._data):
            if kk == k:
                self._data[i] = (k, v)
                return
        self._data.append((k, v))

    def delete(self, k: int) -> bool:
        for i, (kk, _) in enumerate(self._data):
            if kk == k:
                self._data.pop(i)
                return True
        return False

    def lookup(self, k: int) -> Any:
        for kk, v in self._data:
            if kk == k:
                return v
        return None

    def __len__(self) -> int:
        return len(self._data)


# ─── (3) Stateful test: Hypothesis generates op sequences and shrinks ───
class StructureMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.candidate = MyStructure()
        self.oracle = OracleImpl()

    @rule(k=st.integers(), v=st.integers())
    def insert(self, k: int, v: int) -> None:
        self.candidate.insert(k, v)
        self.oracle.insert(k, v)

    @rule(k=st.integers())
    def delete(self, k: int) -> None:
        a = self.candidate.delete(k)
        b = self.oracle.delete(k)
        assert a == b, f"delete({k}) disagreed: candidate={a}, oracle={b}"

    @rule(k=st.integers())
    def lookup(self, k: int) -> None:
        a = self.candidate.lookup(k)
        b = self.oracle.lookup(k)
        assert a == b, f"lookup({k}) disagreed: candidate={a}, oracle={b}"

    @invariant()
    def same_size(self) -> None:
        assert len(self.candidate) == len(self.oracle)

    @invariant()
    def invariants_hold(self) -> None:
        assert self.candidate.check_invariants()


TestStructure = StructureMachine.TestCase


# ─── (4) Stateless properties for narrower checks ───
@given(st.lists(st.integers(), unique=True, max_size=200))
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_insert_delete_roundtrip(keys: list[int]) -> None:
    s = MyStructure()
    for k in keys:
        s.insert(k, k)
    for k in keys:
        s.delete(k)
    assert len(s) == 0
    assert s.check_invariants()


@given(st.dictionaries(st.integers(), st.integers(), max_size=200))
def test_iteration_dedup(items: dict[int, int]) -> None:
    s = MyStructure()
    for k, v in items.items():
        s.insert(k, v)
    assert len(s) == len(items)
    for k, v in items.items():
        assert s.lookup(k) == v
