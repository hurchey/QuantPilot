from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .costs import (
    apply_market_impact,
    apply_slippage,
    apply_spread,
    calculate_fee,
    total_execution_price,
)
from .types import TradeEvent


@dataclass(slots=True)
class PortfolioState:
    cash: float
    position_qty: float = 0.0
    avg_entry_price: float = 0.0

    def is_long(self) -> bool:
        return self.position_qty > 0

    def mark_to_market(self, last_price: float) -> float:
        return float(self.cash) + (float(self.position_qty) * float(last_price))

    def buy(
        self,
        *,
        timestamp: datetime,
        symbol: str,
        market_price: float,
        qty: float,
        fees_bps: float,
        slippage_bps: float,
        spread_bps: float = 0.0,
        impact_bps: float = 0.0,
        reason: str | None = None,
    ) -> TradeEvent | None:
        qty = float(qty)
        if qty <= 0:
            return None

        exec_price = total_execution_price(
            market_price, "buy", slippage_bps, spread_bps, impact_bps
        )
        notional = exec_price * qty
        fee = calculate_fee(notional, fees_bps)
        total_cost = notional + fee

        # Clip quantity if the requested qty is too high for available cash
        if total_cost > self.cash:
            # Approximate max affordable qty (includes fee impact)
            fee_mult = 1.0 + (fees_bps / 10_000.0)
            max_qty = self.cash / (exec_price * fee_mult) if exec_price > 0 else 0.0
            qty = max_qty
            if qty <= 0:
                return None
            notional = exec_price * qty
            fee = calculate_fee(notional, fees_bps)
            total_cost = notional + fee
            if total_cost > self.cash:
                return None

        prev_qty = self.position_qty
        prev_avg = self.avg_entry_price

        self.cash -= total_cost
        self.position_qty += qty

        if self.position_qty > 0:
            if prev_qty <= 0:
                self.avg_entry_price = exec_price
            else:
                self.avg_entry_price = ((prev_qty * prev_avg) + (qty * exec_price)) / self.position_qty

        return TradeEvent(
            timestamp=timestamp,
            symbol=symbol,
            side="buy",
            qty=qty,
            price=exec_price,
            fee=fee,
            realized_pnl=None,
            reason=reason,
        )

    def sell_all(
        self,
        *,
        timestamp: datetime,
        symbol: str,
        market_price: float,
        fees_bps: float,
        slippage_bps: float,
        spread_bps: float = 0.0,
        impact_bps: float = 0.0,
        reason: str | None = None,
    ) -> TradeEvent | None:
        if self.position_qty <= 0:
            return None

        qty = self.position_qty
        exec_price = total_execution_price(
            market_price, "sell", slippage_bps, spread_bps, impact_bps
        )
        notional = exec_price * qty
        fee = calculate_fee(notional, fees_bps)

        realized_pnl = (exec_price - self.avg_entry_price) * qty - fee

        self.cash += notional - fee
        self.position_qty = 0.0
        self.avg_entry_price = 0.0

        return TradeEvent(
            timestamp=timestamp,
            symbol=symbol,
            side="sell",
            qty=qty,
            price=exec_price,
            fee=fee,
            realized_pnl=realized_pnl,
            reason=reason,
        )