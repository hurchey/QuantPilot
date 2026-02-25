from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .metrics import compute_metrics
from .portfolio import PortfolioState
from .signals import generate_sma_crossover_positions
from .types import BacktestConfig, BacktestResult, Bar, EquityPoint


def _coerce_trade_qty(cash: float, price: float, config: BacktestConfig) -> float:
    if price <= 0:
        return 0.0

    if config.fixed_qty is not None:
        qty = float(config.fixed_qty)
    else:
        # approximate all-in qty; actual fee clipping happens inside PortfolioState.buy()
        qty = cash / float(price)

    if not config.allow_fractional:
        qty = float(int(qty))

    return max(qty, 0.0)


def run_backtest(
    *,
    bars: list[Bar],
    positions: list[int],
    config: BacktestConfig,
    meta: dict[str, Any] | None = None,
) -> BacktestResult:
    if not bars:
        return BacktestResult(
            symbol=config.symbol,
            timeframe=config.timeframe,
            config=asdict(config),
            metrics={},
            trades=[],
            equity_curve=[],
            meta=meta or {},
        )

    if len(positions) != len(bars):
        raise ValueError("positions length must match bars length")

    portfolio = PortfolioState(cash=float(config.initial_capital))
    trades = []
    equity_curve: list[EquityPoint] = []

    for i, bar in enumerate(bars):
        desired_pos = 1 if positions[i] else 0
        current_pos = 1 if portfolio.is_long() else 0

        # Position transitions (long/flat only)
        if desired_pos == 1 and current_pos == 0:
            qty = _coerce_trade_qty(portfolio.cash, bar.close, config)
            trade = portfolio.buy(
                timestamp=bar.timestamp,
                symbol=config.symbol,
                market_price=bar.close,
                qty=qty,
                fees_bps=config.fees_bps,
                slippage_bps=config.slippage_bps,
                reason="signal_enter",
            )
            if trade:
                trades.append(trade)

        elif desired_pos == 0 and current_pos == 1:
            trade = portfolio.sell_all(
                timestamp=bar.timestamp,
                symbol=config.symbol,
                market_price=bar.close,
                fees_bps=config.fees_bps,
                slippage_bps=config.slippage_bps,
                reason="signal_exit",
            )
            if trade:
                trades.append(trade)

        # Mark equity after any trade on this bar
        equity = portfolio.mark_to_market(bar.close)
        equity_curve.append(
            EquityPoint(
                timestamp=bar.timestamp,
                equity=equity,
                cash=portfolio.cash,
                position_qty=portfolio.position_qty,
                position_avg_price=portfolio.avg_entry_price,
                drawdown=0.0,
            )
        )

    # Optional final close to realize PnL
    if config.close_final_position and portfolio.is_long():
        last_bar = bars[-1]
        trade = portfolio.sell_all(
            timestamp=last_bar.timestamp,
            symbol=config.symbol,
            market_price=last_bar.close,
            fees_bps=config.fees_bps,
            slippage_bps=config.slippage_bps,
            reason="final_close",
        )
        if trade:
            trades.append(trade)
            # overwrite last point equity after final liquidation
            final_equity = portfolio.mark_to_market(last_bar.close)
            equity_curve[-1] = EquityPoint(
                timestamp=last_bar.timestamp,
                equity=final_equity,
                cash=portfolio.cash,
                position_qty=portfolio.position_qty,
                position_avg_price=portfolio.avg_entry_price,
                drawdown=0.0,
            )

    # Compute drawdown series
    peak = equity_curve[0].equity if equity_curve else 0.0
    for point in equity_curve:
        peak = max(peak, point.equity)
        point.drawdown = (point.equity / peak - 1.0) if peak > 0 else 0.0

    metrics = compute_metrics(
        equity_curve=equity_curve,
        trades=trades,
        bars=bars,
        periods_per_year=config.periods_per_year,
        risk_free_rate=config.risk_free_rate,
    )

    return BacktestResult(
        symbol=config.symbol,
        timeframe=config.timeframe,
        config=asdict(config),
        metrics=metrics,
        trades=trades,
        equity_curve=equity_curve,
        meta=meta or {},
    )


def run_sma_crossover_backtest(
    *,
    bars: list[Bar],
    config: BacktestConfig,
    fast_window: int,
    slow_window: int,
) -> BacktestResult:
    signal_pack = generate_sma_crossover_positions(
        bars=bars,
        fast_window=fast_window,
        slow_window=slow_window,
        shift_for_execution=True,
    )

    positions = signal_pack["positions"]
    assert isinstance(positions, list)

    meta = {
        "strategy_type": "sma_crossover",
        "fast_window": fast_window,
        "slow_window": slow_window,
    }

    return run_backtest(
        bars=bars,
        positions=[int(x) for x in positions],
        config=config,
        meta=meta,
    )