"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";

export type BacktestRun = {
  id: number | string;
  strategy_name?: string;
  symbol?: string;
  timeframe?: string;
  status?: string;
  created_at?: string;
  total_pnl?: number;
  sharpe_ratio?: number;
  win_rate?: number;
  max_drawdown?: number;
  total_trades?: number;
};

export type TradeRow = {
  id: number | string;
  symbol?: string;
  side?: string;
  entry_time?: string;
  exit_time?: string;
  entry_price?: number;
  exit_price?: number;
  quantity?: number;
  pnl?: number;
  return_pct?: number;
};

export type CurvePoint = {
  x: string; // timestamp label
  y: number; // value
};

export type DashboardStats = {
  totalRuns: number;
  completedRuns: number;
  totalTrades: number;
  cumulativePnl: number;
  avgSharpe: number;
  avgWinRate: number;
  maxDrawdown: number;
  bestRunPnl: number;
};

function asArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function toNum(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function normalizeRuns(input: unknown): BacktestRun[] {
  const rows = asArray<Record<string, unknown>>(input);

  return rows.map((r, idx) => {
    const metrics =
      r.metrics && typeof r.metrics === "object"
        ? (r.metrics as Record<string, unknown>)
        : {};

    return {
      id: (r.id as number | string) ?? idx,
      strategy_name: String(
        r.strategy_name ?? r.strategyName ?? r.name ?? r.strategy ?? ""
      ),
      symbol: String(r.symbol ?? ""),
      timeframe: String(r.timeframe ?? ""),
      status: String(r.status ?? "completed"),
      created_at: String(r.created_at ?? r.createdAt ?? ""),
      total_pnl: toNum(r.total_pnl ?? r.totalPnl ?? metrics.total_pnl ?? metrics.pnl, 0),
      sharpe_ratio: toNum(r.sharpe_ratio ?? r.sharpe ?? metrics.sharpe_ratio ?? metrics.sharpe, 0),
      win_rate: toNum(r.win_rate ?? r.winRate ?? metrics.win_rate, 0),
      max_drawdown: toNum(
        r.max_drawdown ?? r.maxDrawdown ?? metrics.max_drawdown,
        0
      ),
      total_trades: toNum(r.total_trades ?? r.totalTrades ?? metrics.total_trades, 0),
    };
  });
}

function normalizeTrades(input: unknown): TradeRow[] {
  const rows = asArray<Record<string, unknown>>(input);

  return rows.map((t, idx) => ({
    id: (t.id as number | string) ?? idx,
    symbol: String(t.symbol ?? ""),
    side: String(t.side ?? t.direction ?? ""),
    entry_time: String(t.entry_time ?? t.entryTime ?? ""),
    exit_time: String(t.exit_time ?? t.exitTime ?? ""),
    entry_price: toNum(t.entry_price ?? t.entryPrice, 0),
    exit_price: toNum(t.exit_price ?? t.exitPrice, 0),
    quantity: toNum(t.quantity ?? t.qty, 0),
    pnl: toNum(t.pnl, 0),
    return_pct: toNum(t.return_pct ?? t.returnPct, 0),
  }));
}

function normalizeCurve(input: unknown): CurvePoint[] {
  const rows = asArray<Record<string, unknown>>(input);

  return rows
    .map((p, idx) => {
      // support shapes like {x,y}, {timestamp,value}, {date,equity}
      const x =
        (p.x as string) ??
        (p.timestamp as string) ??
        (p.date as string) ??
        `#${idx + 1}`;
      const y = toNum(p.y ?? p.value ?? p.equity ?? p.drawdown, 0);
      return { x: String(x), y };
    })
    .filter((p) => Number.isFinite(p.y));
}

function deriveCurvesFromTrades(trades: TradeRow[]) {
  if (!trades.length) {
    return { equityCurve: [] as CurvePoint[], drawdownCurve: [] as CurvePoint[] };
  }

  const sorted = [...trades].sort((a, b) => {
    const ta = new Date(a.exit_time || a.entry_time || "").getTime();
    const tb = new Date(b.exit_time || b.entry_time || "").getTime();
    return ta - tb;
  });

  let cumulative = 0;
  let peak = 0;

  const equityCurve: CurvePoint[] = [];
  const drawdownCurve: CurvePoint[] = [];

  sorted.forEach((t, i) => {
    cumulative += toNum(t.pnl, 0);
    peak = Math.max(peak, cumulative);

    const dd = peak === 0 ? 0 : ((cumulative - peak) / Math.abs(peak || 1)) * 100;
    const label =
      t.exit_time ||
      t.entry_time ||
      `Trade ${i + 1}`;

    equityCurve.push({ x: label, y: cumulative });
    drawdownCurve.push({ x: label, y: dd });
  });

  return { equityCurve, drawdownCurve };
}

export function useDashboard() {
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | number | null>(null);

  const [trades, setTrades] = useState<TradeRow[]>([]);
  const [equityCurve, setEquityCurve] = useState<CurvePoint[]>([]);
  const [drawdownCurve, setDrawdownCurve] = useState<CurvePoint[]>([]);

  const [loading, setLoading] = useState(true);
  const [tradesLoading, setTradesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRun = useMemo(
    () => runs.find((r) => String(r.id) === String(selectedRunId)) ?? null,
    [runs, selectedRunId]
  );

  const stats = useMemo<DashboardStats>(() => {
    const completed = runs.filter((r) => (r.status || "").toLowerCase() !== "failed");
    const totalTrades = runs.reduce((sum, r) => sum + toNum(r.total_trades, 0), 0);
    const cumulativePnl = runs.reduce((sum, r) => sum + toNum(r.total_pnl, 0), 0);

    const sharpeVals = runs
      .map((r) => toNum(r.sharpe_ratio, NaN))
      .filter((v) => Number.isFinite(v));
    const winRateVals = runs
      .map((r) => toNum(r.win_rate, NaN))
      .filter((v) => Number.isFinite(v));
    const maxDrawdowns = runs.map((r) => toNum(r.max_drawdown, 0));
    const pnls = runs.map((r) => toNum(r.total_pnl, 0));

    return {
      totalRuns: runs.length,
      completedRuns: completed.length,
      totalTrades,
      cumulativePnl,
      avgSharpe:
        sharpeVals.length > 0
          ? sharpeVals.reduce((a, b) => a + b, 0) / sharpeVals.length
          : 0,
      avgWinRate:
        winRateVals.length > 0
          ? winRateVals.reduce((a, b) => a + b, 0) / winRateVals.length
          : 0,
      maxDrawdown: maxDrawdowns.length ? Math.min(...maxDrawdowns) : 0,
      bestRunPnl: pnls.length ? Math.max(...pnls) : 0,
    };
  }, [runs]);

  const loadRuns = useCallback(async () => {
    setError(null);

    // Try common route shapes
    let runsRes: unknown;
    try {
      runsRes = await apiFetch("/quant/backtests");
    } catch {
      runsRes = await apiFetch("/backtests");
    }

    const normalized = normalizeRuns(runsRes);
    setRuns(normalized);

    // preserve selection if still exists, otherwise select first
    if (!normalized.length) {
      setSelectedRunId(null);
      return;
    }

    const stillExists = normalized.some(
      (r) => String(r.id) === String(selectedRunId)
    );

    if (!stillExists) {
      setSelectedRunId(normalized[0].id);
    }
  }, [selectedRunId]);

  const loadSelectedRunDetails = useCallback(async (runId: string | number | null) => {
    if (runId == null) {
      setTrades([]);
      setEquityCurve([]);
      setDrawdownCurve([]);
      return;
    }

    setTradesLoading(true);

    try {
      // trades endpoint
      let tradesRes: unknown = [];
      try {
        tradesRes = await apiFetch(`/quant/backtests/${runId}/trades`);
      } catch {
        try {
          tradesRes = await apiFetch(`/backtests/${runId}/trades`);
        } catch {
          tradesRes = [];
        }
      }

      const normalizedTrades = normalizeTrades(tradesRes);
      setTrades(normalizedTrades);

      // equity/drawdown endpoints (optional)
      let eqCurve: CurvePoint[] = [];
      let ddCurve: CurvePoint[] = [];

      try {
        const eqRes = await apiFetch(`/quant/backtests/${runId}/equity-curve`);
        eqCurve = normalizeCurve(eqRes);
      } catch {
        try {
          const eqResAlt = await apiFetch(`/backtests/${runId}/equity-curve`);
          eqCurve = normalizeCurve(eqResAlt);
        } catch {
          // ignore
        }
      }

      try {
        const ddRes = await apiFetch(`/quant/backtests/${runId}/drawdown`);
        ddCurve = normalizeCurve(ddRes);
      } catch {
        try {
          const ddResAlt = await apiFetch(`/backtests/${runId}/drawdown`);
          ddCurve = normalizeCurve(ddResAlt);
        } catch {
          // ignore
        }
      }

      // If backend doesn't expose curves, derive from trades
      if (!eqCurve.length || !ddCurve.length) {
        const derived = deriveCurvesFromTrades(normalizedTrades);
        if (!eqCurve.length) eqCurve = derived.equityCurve;
        if (!ddCurve.length) ddCurve = derived.drawdownCurve;
      }

      setEquityCurve(eqCurve);
      setDrawdownCurve(ddCurve);
    } catch (e) {
      setTrades([]);
      setEquityCurve([]);
      setDrawdownCurve([]);

      const msg = e instanceof Error ? e.message : "Failed to load run details.";
      setError(msg);
    } finally {
      setTradesLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      await loadRuns();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load dashboard.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [loadRuns]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    loadSelectedRunDetails(selectedRunId);
  }, [selectedRunId, loadSelectedRunDetails]);

  return {
    // state
    loading,
    tradesLoading,
    error,
    runs,
    selectedRunId,
    selectedRun,
    trades,
    equityCurve,
    drawdownCurve,
    stats,

    // actions
    setSelectedRunId,
    refresh,
    setError,
  };
}