"""Hybrid PHQ-9 short-form estimators and PHQ-9 severity classification.

The hybrid selects 5 of the 9 PHQ-9 items: 3 FIXED core items + 2 RANDOM items,
and estimates the full 9-item total on the native 0..27 scale.

Weighted-mean estimator (primary), parameterised by alpha = weight on the fixed block:

    T_hat(alpha) = 9 * [ (alpha/3) * sum_F(x) + ((1-alpha)/2) * sum_R(x) ]   in [0, 27]

    alpha = 0.6  ->  equal per-item weight (unbiased neutral estimator)
    alpha = 0.7  ->  danjam's original core-emphasis value

Block-unbiased estimator (baseline):

    T_hat = sum_F(x) + 3 * sum_R(x)     (fixed = census, random = sample of 6 scaled x3)

PHQ-9 standard severity cutoffs on the 0..27 scale:
    0-4 none | 5-9 mild | 10-14 moderate | 15-19 mod-severe | 20-27 severe
"""
from __future__ import annotations

import numpy as np

# Fixed core items: q1 (anhedonia/interest), q2 (depressed mood), q3 (sleep).
# 0-indexed positions into a 9-length item vector.
FIXED_IDX = (0, 1, 2)
RANDOM_POOL = (3, 4, 5, 6, 7, 8)  # remaining 6 items

# PHQ-9 severity bins on the 0..27 scale (right-open upper edges).
SEVERITY_EDGES = (5, 10, 15, 20)
SEVERITY_LABELS = ("none", "mild", "moderate", "mod-severe", "severe")

# Clinically standard "probable depression" screening threshold.
PROBABLE_CUT = 10


def classify(total: np.ndarray) -> np.ndarray:
    """Map 0..27 totals to ordinal severity levels 0..4."""
    return np.digitize(total, SEVERITY_EDGES).astype(int)


def probable(total: np.ndarray) -> np.ndarray:
    """Binary probable-depression flag at the standard >=10 cut."""
    return (np.asarray(total) >= PROBABLE_CUT).astype(int)


def t_hat(five_sum) -> np.ndarray:
    """Equal-weight estimator (paper Code 3-1): rescale the 5-item sum to 0..27.

    Algebraically identical to t_hat_weighted(fixed_sum, random_sum, alpha=0.6).
    """
    return 9.0 * np.asarray(five_sum, dtype=float) / 5.0


def t_hat_weighted(fixed_sum, random_sum, alpha: float) -> np.ndarray:
    """Normalised weighted-mean estimator on the 0..27 scale."""
    fixed_sum = np.asarray(fixed_sum, dtype=float)
    random_sum = np.asarray(random_sum, dtype=float)
    return 9.0 * ((alpha / 3.0) * fixed_sum + ((1.0 - alpha) / 2.0) * random_sum)


def t_hat_block(fixed_sum, random_sum) -> np.ndarray:
    """Block-unbiased estimator: fixed measured in full, random sampled from 6 (x3)."""
    fixed_sum = np.asarray(fixed_sum, dtype=float)
    random_sum = np.asarray(random_sum, dtype=float)
    return fixed_sum + 3.0 * random_sum


def sample_random_indices(rng: np.random.Generator, k: int = 2) -> np.ndarray:
    """Draw k distinct item indices from the random pool."""
    return rng.choice(RANDOM_POOL, size=k, replace=False)


def hybrid_score(items: np.ndarray, random_idx, alpha: float, estimator: str = "weighted") -> np.ndarray:
    """Compute a hybrid estimate for each respondent.

    items      : (N, 9) array of PHQ-9 item scores
    random_idx : iterable of the 2 random-item column indices (shared across respondents)
    estimator  : "weighted" (alpha) or "block"
    """
    items = np.asarray(items, dtype=float)
    fixed_sum = items[:, list(FIXED_IDX)].sum(axis=1)
    random_sum = items[:, list(random_idx)].sum(axis=1)
    if estimator == "weighted":
        return t_hat_weighted(fixed_sum, random_sum, alpha)
    if estimator == "block":
        return t_hat_block(fixed_sum, random_sum)
    raise ValueError(f"unknown estimator: {estimator}")
