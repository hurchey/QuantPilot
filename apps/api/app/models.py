# apps/api/app/models.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    workspace = relationship(
        "Workspace",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    name = Column(String(255), nullable=False, default="Default Workspace")

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="workspace")

    strategies = relationship("Strategy", back_populates="workspace", cascade="all, delete-orphan")
    market_bars = relationship("MarketBar", back_populates="workspace", cascade="all, delete-orphan")
    backtest_runs = relationship("BacktestRun", back_populates="workspace", cascade="all, delete-orphan")
    option_chain_snapshots = relationship(
        "OptionChainSnapshot", back_populates="workspace", cascade="all, delete-orphan"
    )


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    strategy_type = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, default="1d")
    parameters_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="strategies")
    backtest_runs = relationship("BacktestRun", back_populates="strategy", cascade="all, delete-orphan")


class MarketBar(Base):
    __tablename__ = "market_bars"
    __table_args__ = (
        UniqueConstraint("workspace_id", "symbol", "timeframe", "timestamp", name="uq_market_bar"),
        Index("ix_market_bars_ws_symbol_tf_ts", "workspace_id", "symbol", "timeframe", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, default="1d", index=True)

    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False, default=0.0)

    workspace = relationship("Workspace", back_populates="market_bars")


class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    initial_capital = Column(Float, nullable=False)
    fees_bps = Column(Float, nullable=False, default=1.0)
    slippage_bps = Column(Float, nullable=False, default=1.0)

    status = Column(String(50), nullable=False, default="completed")
    metrics_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    workspace = relationship("Workspace", back_populates="backtest_runs")
    strategy = relationship("Strategy", back_populates="backtest_runs")

    trades = relationship("Trade", back_populates="backtest_run", cascade="all, delete-orphan")
    equity_points = relationship("EquityPoint", back_populates="backtest_run", cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    qty = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    fee = Column(Float, nullable=False, default=0.0)
    realized_pnl = Column(Float, nullable=True)

    backtest_run = relationship("BacktestRun", back_populates="trades")


class EquityPoint(Base):
    __tablename__ = "equity_points"

    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True)

    timestamp = Column(DateTime, nullable=False, index=True)
    equity = Column(Float, nullable=False)
    drawdown = Column(Float, nullable=False, default=0.0)

    backtest_run = relationship("BacktestRun", back_populates="equity_points")


# --- Options Quant Data Layer (Phase A) ---


class OptionChainSnapshot(Base):
    """
    Stored option chain snapshot for a symbol at a point in time.
    One row per option (call or put) per strike per expiry.
    """

    __tablename__ = "option_chain_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "symbol", "snapshot_at", "expiry", "option_type", "strike",
            name="uq_option_chain_snapshot",
        ),
        Index(
            "ix_option_chain_ws_symbol_at",
            "workspace_id", "symbol", "snapshot_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)

    symbol = Column(String(50), nullable=False, index=True)
    snapshot_at = Column(DateTime, nullable=False, index=True)

    expiry = Column(DateTime, nullable=False, index=True)  # expiration date
    option_type = Column(String(10), nullable=False)  # "call" or "put"
    strike = Column(Float, nullable=False)

    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    last = Column(Float, nullable=True)
    volume = Column(Float, nullable=True, default=0.0)
    open_interest = Column(Float, nullable=True, default=0.0)
    implied_volatility = Column(Float, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="option_chain_snapshots")


class RiskFreeRate(Base):
    """
    Risk-free rate by date (e.g. SOFR, T-bill).
    Used for options pricing and Greeks.
    """

    __tablename__ = "risk_free_rates"
    __table_args__ = (UniqueConstraint("rate_date", name="uq_risk_free_rate_date"),)

    id = Column(Integer, primary_key=True, index=True)
    rate_date = Column(DateTime, nullable=False, unique=True, index=True)  # date only
    rate = Column(Float, nullable=False)  # decimal, e.g. 0.05 for 5%
    source = Column(String(50), nullable=True)  # e.g. "config", "fred"


class Dividend(Base):
    """
    Dividend by symbol and ex-date.
    Used for options pricing (discrete dividends) and corporate action adjustments.
    """

    __tablename__ = "dividends"
    __table_args__ = (UniqueConstraint("symbol", "ex_date", name="uq_dividend_symbol_exdate"),)

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    ex_date = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=True, default="USD")


# --- Extreme Dislocation Research ---


class DislocationEvent(Base):
    """
    A single extreme upside dislocation event for a U.S.-listed equity.
    Label A: 3-day return >= 500%
    Label B: 3-day return >= 1000%
    """

    __tablename__ = "dislocation_events"
    __table_args__ = (
        UniqueConstraint("symbol", "event_start_date", name="uq_dislocation_event"),
        Index("ix_dislocation_symbol_date", "symbol", "event_start_date"),
    )

    id = Column(Integer, primary_key=True, index=True)

    # Core identity
    symbol = Column(String(50), nullable=False, index=True)
    company_name = Column(String(500), nullable=True)
    security_type = Column(String(50), nullable=True)  # common, ADR, SPAC, closed-end fund, etc.

    # Event window
    event_start_date = Column(DateTime, nullable=False, index=True)
    event_end_date = Column(DateTime, nullable=False)
    peak_date = Column(DateTime, nullable=True)

    # Price data
    price_start = Column(Float, nullable=False)
    price_peak = Column(Float, nullable=False)
    price_end_3d = Column(Float, nullable=True)  # close on day 3
    return_1d_pct = Column(Float, nullable=True)
    return_3d_pct = Column(Float, nullable=False)  # the qualifying return
    return_peak_pct = Column(Float, nullable=True)  # intraday high vs start close

    # Labels
    label_a = Column(Integer, nullable=False, default=0)  # 1 if 3d return >= 500%
    label_b = Column(Integer, nullable=False, default=0)  # 1 if 3d return >= 1000%
    day_after_continuation = Column(Integer, nullable=True)  # 1=up, 0=down on day 4

    # Volume profile
    volume_event_day = Column(Float, nullable=True)
    volume_avg_20d_pre = Column(Float, nullable=True)  # 20-day avg volume before event
    volume_ratio = Column(Float, nullable=True)  # event day vol / avg

    # Float & structure
    shares_outstanding = Column(Float, nullable=True)
    float_shares = Column(Float, nullable=True)
    market_cap_pre = Column(Float, nullable=True)  # market cap before event
    short_interest_shares = Column(Float, nullable=True)
    short_pct_float = Column(Float, nullable=True)
    days_to_cover = Column(Float, nullable=True)

    # Fundamentals
    sector = Column(String(100), nullable=True)
    industry = Column(String(200), nullable=True)
    exchange = Column(String(50), nullable=True)
    ipo_date = Column(DateTime, nullable=True)
    days_since_ipo = Column(Integer, nullable=True)

    # Attention / news
    catalyst_summary = Column(String(2000), nullable=True)  # manual or NLP-extracted
    news_count_event_day = Column(Integer, nullable=True)

    # Options context
    options_available = Column(Integer, nullable=True)  # 1=yes, 0=no
    iv_pre_event = Column(Float, nullable=True)
    call_oi_pre = Column(Float, nullable=True)
    put_oi_pre = Column(Float, nullable=True)

    # Taxonomy
    taxonomy_bucket = Column(String(100), nullable=True, index=True)
    taxonomy_confidence = Column(Float, nullable=True)
    taxonomy_notes = Column(String(2000), nullable=True)

    # Meta
    data_source = Column(String(100), nullable=True)  # yfinance, manual, SEC, etc.
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    features = relationship("DislocationFeature", back_populates="event", cascade="all, delete-orphan")


class DislocationFeature(Base):
    """
    Extensible key-value feature store for dislocation events.
    Allows adding arbitrary features without schema migrations.
    """

    __tablename__ = "dislocation_features"
    __table_args__ = (
        UniqueConstraint("event_id", "feature_name", name="uq_dislocation_feature"),
    )

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("dislocation_events.id", ondelete="CASCADE"), nullable=False, index=True)

    feature_name = Column(String(200), nullable=False, index=True)
    feature_value = Column(String(2000), nullable=True)
    feature_numeric = Column(Float, nullable=True)
    feature_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)

    event = relationship("DislocationEvent", back_populates="features")