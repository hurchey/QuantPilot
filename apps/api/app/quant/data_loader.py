from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..models import MarketBar
from .types import Bar


def load_market_bars(
    *,
    db: Session,
    workspace_id: int,
    symbol: str,
    timeframe: str = "1d",
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
    limit: int | None = None,
) -> list[Bar]:
    """
    Loads historical bars from your SQLAlchemy MarketBar model and returns quant Bar objects.
    Assumes MarketBar has fields:
      workspace_id, symbol, timeframe, timestamp, open, high, low, close, volume
    """
    q = (
        db.query(MarketBar)
        .filter(MarketBar.workspace_id == workspace_id)
        .filter(MarketBar.symbol == symbol)
        .filter(MarketBar.timeframe == timeframe)
    )

    if start_dt is not None:
        q = q.filter(MarketBar.timestamp >= start_dt)
    if end_dt is not None:
        q = q.filter(MarketBar.timestamp <= end_dt)

    q = q.order_by(MarketBar.timestamp.asc())

    if limit is not None and limit > 0:
        q = q.limit(limit)

    rows = q.all()

    bars: list[Bar] = []
    seen_ts: set[datetime] = set()

    for row in rows:
        ts = row.timestamp
        if ts in seen_ts:
            # skip duplicates by timestamp
            continue
        seen_ts.add(ts)

        bars.append(
            Bar(
                timestamp=ts,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume or 0.0),
            )
        )

    return bars