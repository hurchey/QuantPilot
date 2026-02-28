"""
Trade analysis: learn from wins and losses.

Extracts why trades won or lost for strategy improvement:
- Entry/exit context (price move, volatility, holding period)
- Attribution: timing vs signal quality
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .types import Bar, TradeEvent


@dataclass(slots=True)
class TradeContext:
    """Context around a single round-trip trade."""

    symbol: str
    entry_ts: datetime
    exit_ts: datetime
    side: str  # "long" | "short"
    entry_price: float
    exit_price: float
    qty: float
    fee: float
    realized_pnl: float
    holding_bars: int
    price_return_pct: float  # (exit - entry) / entry * 100
    max_favorable_excursion: float  # best price move in our favor
    max_adverse_excursion: float  # worst price move against us
    bars: list[Bar] = field(repr=False)
    win: bool
    attribution: str  # "timing" | "signal" | "costs" | "mixed"


def analyze_round_trip(
    buy_trade: TradeEvent,
    sell_trade: TradeEvent,
    bars: list[Bar],
) -> TradeContext | None:
    """
    Analyze a buy->sell round trip. bars should cover [entry_ts, exit_ts].
    """
    if buy_trade.side != "buy" or sell_trade.side != "sell":
        return None

    entry_ts = buy_trade.timestamp
    exit_ts = sell_trade.timestamp
    entry_price = buy_trade.price
    exit_price = sell_trade.price
    qty = buy_trade.qty
    fee = (buy_trade.fee or 0) + (sell_trade.fee or 0)
    pnl = sell_trade.realized_pnl or 0.0

    # Find bars in holding period
    period_bars = [b for b in bars if entry_ts <= b.timestamp <= exit_ts]
    period_bars.sort(key=lambda b: b.timestamp)
    holding_bars = len(period_bars)

    if not period_bars:
        price_return_pct = 0.0
        mfe = 0.0
        mae = 0.0
    else:
        price_return_pct = ((exit_price - entry_price) / entry_price) * 100.0
        highs = [b.high for b in period_bars]
        lows = [b.low for b in period_bars]
        mfe = ((max(highs) - entry_price) / entry_price) * 100.0 if highs else 0.0
        mae = ((min(lows) - entry_price) / entry_price) * 100.0 if lows else 0.0

    win = pnl > 0

    # Simple attribution
    if win:
        if price_return_pct > 0 and fee > 0 and abs(pnl) < fee:
            attribution = "costs"
        elif mfe > abs(mae) * 1.5:
            attribution = "timing"  # caught a good move
        else:
            attribution = "signal"
    else:
        if price_return_pct < 0 and abs(mae) > abs(mfe):
            attribution = "signal"  # wrong direction
        elif price_return_pct > 0 and fee > abs(pnl):
            attribution = "costs"
        else:
            attribution = "mixed"

    return TradeContext(
        symbol=buy_trade.symbol,
        entry_ts=entry_ts,
        exit_ts=exit_ts,
        side="long",
        entry_price=entry_price,
        exit_price=exit_price,
        qty=qty,
        fee=fee,
        realized_pnl=pnl,
        holding_bars=holding_bars,
        price_return_pct=price_return_pct,
        max_favorable_excursion=mfe,
        max_adverse_excursion=mae,
        bars=period_bars,
        win=win,
        attribution=attribution,
    )


def analyze_all_trades(
    trades: list[TradeEvent],
    bars: list[Bar],
) -> list[TradeContext]:
    """Pair buys with sells and analyze each round trip."""
    buys = [t for t in trades if t.side == "buy"]
    sells = [t for t in trades if t.side == "sell"]

    contexts = []
    for b in buys:
        # Find matching sell (next sell after this buy)
        matching_sells = [s for s in sells if s.timestamp > b.timestamp]
        if not matching_sells:
            continue
        s = min(matching_sells, key=lambda x: x.timestamp)
        ctx = analyze_round_trip(b, s, bars)
        if ctx:
            contexts.append(ctx)

    return contexts


def summarize_learning(
    contexts: list[TradeContext],
) -> dict[str, Any]:
    """
    Summarize what we learned from wins and losses.
    """
    wins = [c for c in contexts if c.win]
    losses = [c for c in contexts if not c.win]

    win_attribution = {}
    for c in wins:
        win_attribution[c.attribution] = win_attribution.get(c.attribution, 0) + 1

    loss_attribution = {}
    for c in losses:
        loss_attribution[c.attribution] = loss_attribution.get(c.attribution, 0) + 1

    avg_holding_win = sum(c.holding_bars for c in wins) / len(wins) if wins else 0
    avg_holding_loss = sum(c.holding_bars for c in losses) / len(losses) if losses else 0

    return {
        "num_wins": len(wins),
        "num_losses": len(losses),
        "win_rate": len(wins) / len(contexts) if contexts else 0,
        "win_attribution": win_attribution,
        "loss_attribution": loss_attribution,
        "avg_holding_bars_win": round(avg_holding_win, 1),
        "avg_holding_bars_loss": round(avg_holding_loss, 1),
        "insight": _generate_insight(wins, losses, win_attribution, loss_attribution),
    }


def _generate_insight(
    wins: list[TradeContext],
    losses: list[TradeContext],
    win_attr: dict[str, int],
    loss_attr: dict[str, int],
) -> str:
    """Generate human-readable insight."""
    parts = []
    if loss_attr.get("costs", 0) > len(losses) * 0.3:
        parts.append("Many losses from costs; consider reducing turnover or improving execution.")
    if loss_attr.get("signal", 0) > len(losses) * 0.5:
        parts.append("Losses often from wrong direction; review signal quality.")
    if win_attr.get("timing", 0) > len(wins) * 0.5:
        parts.append("Wins often from good timing; consider trailing stops to lock in MFE.")
    if not parts:
        parts.append("No strong pattern; collect more trades for analysis.")
    return " ".join(parts)
