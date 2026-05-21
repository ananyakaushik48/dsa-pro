"""
Property-test scaffold (Python / hypothesis) using the oracle pattern.

The oracle pattern is the single highest-value test for a custom data structure
(see references/verification.md). Generate a random sequence of operations,
apply it to both your custom structure and a trivially correct reference (the
"oracle"), and assert that observable behavior matches after every op.

To adapt:
  1. Replace `MyStructure` and `Oracle` with your real classes.
  2. Edit the `Op` enum + the generator strategy to match your API.
  3. Implement `apply_op` for both sides.
  4. Implement `observable_state` so the assert compares everything the caller can see.
  5. Implement `check_invariants` to encode the structure's defining property.

Run:
    pip install hypothesis
    pytest scripts/proptest.py
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import pytest
from hypothesis import given, settings, strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    precondition,
    rule,
)


# ---------------------------------------------------------------------------
# 1. Replace these with your real types.
# ---------------------------------------------------------------------------


class MyStructure:
    """The structure under test. Replace with your real impl."""

    def __init__(self) -> None:
        self._items: dict[int, str] = {}

    def insert(self, k: int, v: str) -> None:
        self._items[k] = v

    def delete(self, k: int) -> None:
        self._items.pop(k, None)

    def lookup(self, k: int) -> str | None:
        return self._items.get(k)

    def iter_sorted(self) -> list[tuple[int, str]]:
        return sorted(self._items.items())

    def check_invariants(self) -> bool:
        # Encode the structure's defining property. For a real custom impl this
        # might be "every black node has the same black-height," "load factor
        # within bounds," etc. The placeholder here just sanity-checks types.
        return all(isinstance(k, int) and isinstance(v, str) for k, v in self._items.items())


class Oracle:
    """A trivially correct reference. Speed doesn't matter; correctness does."""

    def __init__(self) -> None:
        self._items: dict[int, str] = {}

    def insert(self, k: int, v: str) -> None:
        self._items[k] = v

    def delete(self, k: int) -> None:
        self._items.pop(k, None)

    def lookup(self, k: int) -> str | None:
        return self._items.get(k)

    def iter_sorted(self) -> list[tuple[int, str]]:
        return sorted(self._items.items())


# ---------------------------------------------------------------------------
# 2. Op model. Edit to match your API.
# ---------------------------------------------------------------------------


class OpKind(Enum):
    INSERT = auto()
    DELETE = auto()
    LOOKUP = auto()
    ITER = auto()


@dataclass(frozen=True)
class Op:
    kind: OpKind
    k: int | None = None
    v: str | None = None


# Generator: build a random op. Tune the weights so deletes and lookups don't
# starve under high insert pressure.
ops_strategy = st.one_of(
    st.builds(Op, kind=st.just(OpKind.INSERT), k=st.integers(min_value=-100, max_value=100), v=st.text(max_size=8)),
    st.builds(Op, kind=st.just(OpKind.DELETE), k=st.integers(min_value=-100, max_value=100)),
    st.builds(Op, kind=st.just(OpKind.LOOKUP), k=st.integers(min_value=-100, max_value=100)),
    st.builds(Op, kind=st.just(OpKind.ITER)),
)


# ---------------------------------------------------------------------------
# 3. Apply + observe.
# ---------------------------------------------------------------------------


def apply_op(structure: Any, op: Op) -> Any:
    """Apply an op and return its observable result (or None for mutators)."""
    if op.kind is OpKind.INSERT:
        structure.insert(op.k, op.v)
        return None
    if op.kind is OpKind.DELETE:
        structure.delete(op.k)
        return None
    if op.kind is OpKind.LOOKUP:
        return structure.lookup(op.k)
    if op.kind is OpKind.ITER:
        return structure.iter_sorted()
    raise AssertionError(f"unknown op: {op.kind}")


def observable_state(structure: Any) -> Any:
    """Everything the caller can see. Used to compare to the oracle."""
    return structure.iter_sorted()


# ---------------------------------------------------------------------------
# 4. The actual property tests.
# ---------------------------------------------------------------------------


@given(ops=st.lists(ops_strategy, max_size=200))
@settings(max_examples=200, deadline=None)
def test_oracle(ops: list[Op]) -> None:
    """For every op sequence, observable behavior matches the oracle and
    invariants hold after every step."""
    custom = MyStructure()
    oracle = Oracle()

    for op in ops:
        r_custom = apply_op(custom, op)
        r_oracle = apply_op(oracle, op)
        assert r_custom == r_oracle, (
            f"op {op} produced {r_custom!r} on custom but {r_oracle!r} on oracle"
        )
        assert custom.check_invariants(), (
            f"invariants violated after op {op}; state: {observable_state(custom)!r}"
        )

    assert observable_state(custom) == observable_state(oracle), (
        f"final state diverged: custom={observable_state(custom)!r} oracle={observable_state(oracle)!r}"
    )


@given(ops=st.lists(ops_strategy, max_size=200))
@settings(max_examples=200, deadline=None)
def test_invariants_hold(ops: list[Op]) -> None:
    """Invariants hold after every op, even without an oracle to compare to."""
    s = MyStructure()
    for op in ops:
        apply_op(s, op)
        assert s.check_invariants(), f"invariants violated after {op}"


@given(items=st.lists(st.tuples(st.integers(), st.text(max_size=8)), max_size=200))
@settings(max_examples=100, deadline=None)
def test_insert_delete_roundtrip(items: list[tuple[int, str]]) -> None:
    """Every key inserted is findable; deleting all keys leaves the structure empty
    (of the inserted keys)."""
    s = MyStructure()
    # Deduplicate by key to match map semantics.
    dedup: dict[int, str] = {}
    for k, v in items:
        s.insert(k, v)
        dedup[k] = v
    for k, v in dedup.items():
        assert s.lookup(k) == v
    for k in dedup:
        s.delete(k)
    for k in dedup:
        assert s.lookup(k) is None


# ---------------------------------------------------------------------------
# 5. Stateful (RuleBasedStateMachine) version — sometimes finds bugs the
#    flat @given style misses. Use when ops interact strongly with state
#    (e.g., a stack where pop only makes sense after push).
# ---------------------------------------------------------------------------


class StructureStateMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.custom = MyStructure()
        self.oracle = Oracle()

    @rule(k=st.integers(min_value=-100, max_value=100), v=st.text(max_size=8))
    def insert(self, k: int, v: str) -> None:
        self.custom.insert(k, v)
        self.oracle.insert(k, v)

    @rule(k=st.integers(min_value=-100, max_value=100))
    def delete(self, k: int) -> None:
        self.custom.delete(k)
        self.oracle.delete(k)

    @rule(k=st.integers(min_value=-100, max_value=100))
    def lookup(self, k: int) -> None:
        assert self.custom.lookup(k) == self.oracle.lookup(k)

    @invariant()
    def invariants(self) -> None:
        assert self.custom.check_invariants()
        assert self.custom.iter_sorted() == self.oracle.iter_sorted()


TestStructureStateMachine = StructureStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
