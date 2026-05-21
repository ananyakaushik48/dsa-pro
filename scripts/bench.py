"""
Microbench scaffold (Python / pytest-benchmark) with the discipline from
references/verification.md → Microbench discipline.

What this scaffold gets right (so you don't have to remember every time):
  * Defeats dead-code elimination by accumulating a side-effecting result.
  * Sweeps the access pattern: sequential, random, zipfian (skewed).
  * Sweeps the working-set size to expose cache effects.
  * Reports median + IQR (pytest-benchmark does this by default).
  * Includes a guard for hostile environments (CPU throttling, noise) — see
    the README block at the bottom for the runner command.

To adapt:
  1. Replace `MyStructure` with your real impl.
  2. Adjust `WORKLOAD_SIZES` and `DISTRIBUTIONS` to match what you care about.
  3. Add benches for the specific operations on your hot path.
  4. Run with `pytest scripts/bench.py --benchmark-only --benchmark-columns=median,iqr,outliers,rounds,iterations`.

Install:
  pip install pytest pytest-benchmark numpy

Run with environment hardened:
  taskset -c 0 nice -n -20 \\
    pytest scripts/bench.py --benchmark-only \\
      --benchmark-columns=median,iqr,outliers,rounds,iterations \\
      --benchmark-warmup=on --benchmark-warmup-iterations=1000
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from typing import Any

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# 1. Replace with your real structure.
# ---------------------------------------------------------------------------


class MyStructure:
    """The structure under test. Replace with your real impl."""

    def __init__(self) -> None:
        self._items: dict[int, int] = {}

    def insert(self, k: int, v: int) -> None:
        self._items[k] = v

    def lookup(self, k: int) -> int | None:
        return self._items.get(k)

    def delete(self, k: int) -> None:
        self._items.pop(k, None)


# ---------------------------------------------------------------------------
# 2. Workload generators. Same shape for every bench — change the distribution
#    to expose how the structure responds to different access patterns.
# ---------------------------------------------------------------------------


WORKLOAD_SIZES = [1_000, 10_000, 100_000]
DISTRIBUTIONS = ["sequential", "random", "zipfian"]


def gen_keys(n: int, distribution: str, seed: int = 0xC0FFEE) -> np.ndarray:
    """Generate n keys with a given access distribution. Same seed → same
    keys (for repeatable benches)."""
    rng = np.random.default_rng(seed)
    if distribution == "sequential":
        return np.arange(n, dtype=np.int64)
    if distribution == "random":
        return rng.integers(low=0, high=n * 10, size=n, dtype=np.int64)
    if distribution == "zipfian":
        # Power-law / "heavy hitter" distribution: a few keys dominate.
        zs = rng.zipf(a=1.5, size=n)
        return (zs % (n * 10)).astype(np.int64)
    raise ValueError(f"unknown distribution: {distribution}")


def populate(s: Any, keys: Iterable[int]) -> None:
    for i, k in enumerate(keys):
        s.insert(int(k), i)


# ---------------------------------------------------------------------------
# 3. Black-box accumulator. Forces the JIT / compiler / VM to keep the
#    benchmarked call's result around. Without this, dead-code elimination
#    can silently zero out the loop body.
# ---------------------------------------------------------------------------


_sink = 0


def consume(x: Any) -> None:
    global _sink
    if x is None:
        _sink ^= 1
    else:
        _sink ^= hash(x) & 0xFFFF


def _flush_sink() -> int:
    # Print the sink so the optimizer can't prove it's dead. Called from a
    # pytest fixture at teardown to dump it after each bench.
    return _sink


# ---------------------------------------------------------------------------
# 4. Parametrized benches across (size, distribution).
# ---------------------------------------------------------------------------


@pytest.fixture(params=WORKLOAD_SIZES, ids=lambda n: f"N={n}")
def workload_size(request: pytest.FixtureRequest) -> int:
    return request.param


@pytest.fixture(params=DISTRIBUTIONS, ids=lambda d: f"dist={d}")
def distribution(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture
def populated(workload_size: int, distribution: str) -> tuple[MyStructure, np.ndarray]:
    s = MyStructure()
    keys = gen_keys(workload_size, distribution, seed=0xC0FFEE)
    populate(s, keys)
    return s, keys


def test_bench_lookup(benchmark, populated):
    s, keys = populated
    # Iterate keys in the same distribution to hit the same access pattern at
    # query time. Use a separate seed so lookups don't perfectly align with
    # insertion order on the structure (more realistic).
    query_keys = gen_keys(len(keys), "random", seed=0xBEEF)

    def run():
        for k in query_keys:
            consume(s.lookup(int(k)))

    benchmark(run)


def test_bench_insert(benchmark, workload_size: int, distribution: str):
    keys = gen_keys(workload_size, distribution, seed=0xFACE)

    def run():
        s = MyStructure()
        for i, k in enumerate(keys):
            s.insert(int(k), i)
        consume(len(keys))

    benchmark(run)


def test_bench_mixed(benchmark, populated):
    """80% lookup, 15% insert, 5% delete — a realistic read-heavy workload."""
    s, keys = populated
    ops_keys = gen_keys(len(keys), "random", seed=0xDEAD)
    rng = np.random.default_rng(0xBEEF)
    roll = rng.random(len(keys))

    def run():
        for k, r in zip(ops_keys, roll, strict=False):
            if r < 0.80:
                consume(s.lookup(int(k)))
            elif r < 0.95:
                s.insert(int(k), 1)
            else:
                s.delete(int(k))

    benchmark(run)


# ---------------------------------------------------------------------------
# 5. Hostile-environment guard.
#
#   Modern CPUs throttle and boost dynamically; runs on a noisy laptop will
#   produce IQRs that are useless. The runner command at the top of this file
#   pins to a single core (`taskset -c 0`) and raises priority (`nice`).
#   On Linux, also consider:
#       sudo cpupower frequency-set -g performance
#       sudo sysctl kernel.randomize_va_space=0   # only for measurement
#
#   On macOS (M-series), Time Profiler in Instruments is the trustworthy
#   alternative — bench numbers from raw scripts are noisier than on Linux.
#
#   ALWAYS report the environment alongside the numbers. See the reporting
#   template in references/verification.md.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _print_env_at_end():
    yield
    import platform
    import sys

    print()
    print("# Bench environment")
    print(f"# Python: {sys.version.split()[0]}")
    print(f"# Platform: {platform.platform()}")
    print(f"# CPU: {platform.processor() or 'n/a'}")
    print(f"# Sink (defeats DCE): {_flush_sink():#x}")


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "--benchmark-only",
            "--benchmark-columns=median,iqr,outliers,rounds,iterations",
            "--benchmark-warmup=on",
            "--benchmark-warmup-iterations=1000",
        ]
    )
