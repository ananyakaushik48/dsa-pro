"""
Microbench scaffold (Python + pytest-benchmark).

Install: pip install pytest pytest-benchmark numpy
Run:     pytest bench.py --benchmark-min-rounds=20 --benchmark-warmup=on \\
                       --benchmark-columns=median,iqr_outliers,outliers,ops

Disciplines applied:
  - Distribution sweep: sequential / random / zipfian
  - Working-set sweep: tiny / fits-L2 / spills to DRAM
  - Anti-DCE: accumulate to a sink that the function returns
  - Reports median and IQR, not mean
"""

import random
import pytest
import numpy as np


def seq_keys(n: int) -> list[int]:
    return list(range(n))


def random_keys(n: int) -> list[int]:
    return [random.randint(0, 2**31 - 1) for _ in range(n)]


def zipfian_keys(n: int, alpha: float = 1.1) -> list[int]:
    ranks = np.arange(1, n + 1, dtype=np.float64)
    p = 1 / np.power(ranks, alpha)
    p /= p.sum()
    return list(np.random.choice(n, size=n, p=p))


DISTRIBUTIONS = {
    "sequential": seq_keys,
    "random": random_keys,
    "zipfian": zipfian_keys,
}

WORKING_SETS = {
    "4K": 4_000,
    "64K": 64_000,
    "1M": 1_000_000,
}


@pytest.fixture(scope="module", params=list(WORKING_SETS.items()))
def working_set(request):
    name, n = request.param
    return name, n


@pytest.fixture(scope="module", params=list(DISTRIBUTIONS.items()))
def keys(request, working_set):
    dist_name, dist_fn = request.param
    ws_name, n = working_set
    return f"{dist_name}/{ws_name}", dist_fn(n)


# ─── Replace `do_inserts` / `do_lookups` with the candidate(s). ───
def do_inserts_dict(n: int, ks: list[int]) -> int:
    d: dict[int, int] = {}
    for i in range(n):
        d[ks[i]] = i
    return len(d)  # return = sink (prevents DCE)


def do_lookups_dict(n: int, ks: list[int], built: dict[int, int]) -> int:
    acc = 0
    for i in range(n):
        acc += built.get(ks[i], 0)
    return acc


def test_dict_insert(benchmark, keys):
    label, ks = keys
    n = len(ks)
    benchmark.group = f"insert {label}"
    benchmark(do_inserts_dict, n, ks)


def test_dict_lookup(benchmark, keys):
    label, ks = keys
    n = len(ks)
    built = {k: i for i, k in enumerate(ks)}
    benchmark.group = f"lookup {label}"
    benchmark(do_lookups_dict, n, ks, built)
