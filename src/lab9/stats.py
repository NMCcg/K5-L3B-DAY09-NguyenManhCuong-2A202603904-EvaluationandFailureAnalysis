"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

import inspect
import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy import stats as sp_stats

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    # TODO M2
    tp = fp = fn = tn = 0
    for h, j in zip(human, judge):
        h_pos = (h == POS)
        j_pos = (j == POS)
        if h_pos and j_pos:
            tp += 1
        elif not h_pos and j_pos:
            fp += 1
        elif h_pos and not j_pos:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    # TODO M2: precision = tp/(tp+fp), recall = tp/(tp+fn); return 0.0 when the denominator is 0
    cm = confusion(human, judge)
    tp, fp, fn = cm["tp"], cm["fp"], cm["fn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    # TODO M2
    n = len(human)
    if n == 0 or len(judge) != n:
        raise ValueError("Inputs must be non-empty sequences of equal length")

    p_o = sum(1 for h, j in zip(human, judge) if h == j) / n

    categories = set(human) | set(judge)
    p_e = 0.0
    for c in categories:
        p_h = sum(1 for h in human if h == c) / n
        p_j = sum(1 for j in judge if j == c) / n
        p_e += p_h * p_j

    if abs(1.0 - p_e) < 1e-12:
        raise ValueError("Cohen's kappa is undefined when expected agreement p_e == 1")

    return (p_o - p_e) / (1.0 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    # TODO M2: (p_obs + spec - 1) / (sens + spec - 1)
    denom = sensitivity + specificity - 1.0
    if abs(denom) < 1e-12:
        return max(0.0, min(1.0, float(observed_rate)))
    corrected = (observed_rate + specificity - 1.0) / denom
    return max(0.0, min(1.0, float(corrected)))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    # TODO M4
    if len(a) != len(b):
        raise ValueError("Sequences a and b must have the same length")
    if len(a) == 0:
        return (0.0, 0.0, 0.0)

    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)

    if np.array_equal(a_arr, b_arr):
        return (0.0, 0.0, 0.0)

    d = float(np.mean(a_arr) - np.mean(b_arr))

    def _statistic(x: np.ndarray, y: np.ndarray, axis: int = -1) -> np.ndarray:
        return np.mean(x, axis=axis) - np.mean(y, axis=axis)

    generator = np.random.default_rng(rng)
    sig = inspect.signature(sp_stats.bootstrap)
    kwargs: dict[str, Any] = {
        "paired": True,
        "method": "percentile",
        "confidence_level": confidence,
        "n_resamples": n_resamples,
    }
    if "rng" in sig.parameters:
        kwargs["rng"] = generator
    else:
        kwargs["random_state"] = generator

    res = sp_stats.bootstrap((a_arr, b_arr), _statistic, **kwargs)
    return (d, float(res.confidence_interval.low), float(res.confidence_interval.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    # TODO M6
    if k < 1 or k > n or c < 0 or c > n:
        raise ValueError(f"Invalid arguments for pass_at_k: n={n}, c={c}, k={k}")
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    # TODO M6
    if k < 1 or k > n or c < 0 or c > n:
        raise ValueError(f"Invalid arguments for pass_hat_k: n={n}, c={c}, k={k}")
    if c < k:
        return 0.0
    return math.comb(c, k) / math.comb(n, k)
