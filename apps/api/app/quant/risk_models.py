"""
Risk models: covariance shrinkage, factor exposure.
"""

from __future__ import annotations

from typing import Any


def ledoit_wolf_shrinkage(
    returns: list[list[float]],
    delta: float | None = None,
) -> tuple[list[list[float]], float]:
    """
    Ledoit-Wolf covariance shrinkage toward constant correlation.
    returns: list of asset return series (each same length).
    Returns (shrunk_cov, shrinkage_intensity).
    """
    import math

    n_assets = len(returns)
    if n_assets == 0:
        return ([], 0.0)
    T = len(returns[0])
    if T < 2:
        return ([[0.0] * n_assets for _ in range(n_assets)], 0.0)

    # Sample covariance
    means = [sum(r) / T for r in returns]
    S = [[0.0] * n_assets for _ in range(n_assets)]
    for i in range(n_assets):
        for j in range(n_assets):
            S[i][j] = sum((returns[i][t] - means[i]) * (returns[j][t] - means[j]) for t in range(T)) / (T - 1)

    # Target: constant correlation (F)
    vols = [max(S[i][i] ** 0.5, 1e-10) for i in range(n_assets)]
    avg_corr = 0.0
    count = 0
    for i in range(n_assets):
        for j in range(n_assets):
            if i != j and vols[i] > 0 and vols[j] > 0:
                avg_corr += S[i][j] / (vols[i] * vols[j])
                count += 1
    r_bar = avg_corr / count if count > 0 else 0.0
    F = [[vols[i] * vols[j] * (r_bar if i != j else 1.0) for j in range(n_assets)] for i in range(n_assets)]

    # Shrinkage intensity (simplified)
    if delta is None:
        delta = min(1.0, max(0.0, 1.0 - (n_assets + 1) / T))
    shrunk = [[S[i][j] * (1 - delta) + F[i][j] * delta for j in range(n_assets)] for i in range(n_assets)]
    return (shrunk, delta)


def factor_exposure(
    returns: list[float],
    factor_returns: list[list[float]],
) -> list[float]:
    """
    OLS factor exposures (beta) for one asset vs factors.
    returns: asset return series
    factor_returns: list of factor return series
    """
    n = len(returns)
    k = len(factor_returns)
    if n < 2 or k == 0 or any(len(f) != n for f in factor_returns):
        return [0.0] * k

    # Single factor: beta = cov(r, f) / var(f)
    if k == 1:
        f = factor_returns[0]
        mean_r = sum(returns) / n
        mean_f = sum(f) / n
        cov = sum((returns[i] - mean_r) * (f[i] - mean_f) for i in range(n)) / (n - 1)
        var_f = sum((f[i] - mean_f) ** 2 for i in range(n)) / (n - 1)
        return [cov / var_f] if var_f > 1e-12 else [0.0]

    # Multi-factor: simple correlation-based for k>1
    return [
        sum((returns[i] - sum(returns) / n) * (factor_returns[j][i] - sum(factor_returns[j]) / n) for i in range(n))
        / max(
            sum((factor_returns[j][i] - sum(factor_returns[j]) / n) ** 2 for i in range(n)),
            1e-12,
        )
        for j in range(k)
    ]
