"""
Online updates: EWMA, recursive least squares, Kalman-style.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EWMAState:
    """Exponentially weighted moving average."""

    value: float
    alpha: float


def ewma_update(state: EWMAState, observation: float) -> float:
    """Update EWMA: x_new = alpha * obs + (1-alpha) * x_old."""
    state.value = state.alpha * observation + (1.0 - state.alpha) * state.value
    return state.value


def ewma_init(initial: float, alpha: float = 0.1) -> EWMAState:
    """alpha: 0.1 = slow, 0.3 = medium, 0.5 = fast."""
    return EWMAState(value=initial, alpha=alpha)


@dataclass(slots=True)
class RLSState:
    """Recursive least squares (single regressor)."""

    beta: float
    P: float  # inverse of X'X
    lambda_forget: float  # 0.99 typical


def rls_update(state: RLSState, x: float, y: float) -> float:
    """
    RLS update: y = beta * x.
    Forgetting factor for non-stationary data.
    """
    # P_new = (P_old / lambda) - gain * x * (P_old / lambda)
    # beta_new = beta_old + gain * (y - x * beta_old)
    P = state.P / state.lambda_forget
    gain = P * x / (1.0 + x * P * x)
    state.beta = state.beta + gain * (y - x * state.beta)
    state.P = P - gain * x * P
    return state.beta


def rls_init(beta: float = 0.0, P: float = 1e6, lambda_forget: float = 0.99) -> RLSState:
    return RLSState(beta=beta, P=P, lambda_forget=lambda_forget)


def kalman_1d_update(
    state_mean: float,
    state_var: float,
    observation: float,
    obs_var: float,
    process_var: float,
) -> tuple[float, float]:
    """
    1D Kalman update.
    Returns (new_mean, new_var).
    """
    pred_var = state_var + process_var
    K = pred_var / (pred_var + obs_var)  # Kalman gain
    new_mean = state_mean + K * (observation - state_mean)
    new_var = (1 - K) * pred_var
    return (new_mean, new_var)
