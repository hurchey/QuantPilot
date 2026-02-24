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