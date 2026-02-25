// apps/web/src/hooks/useBacktests.ts
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:3000";

type BacktestRun = {
  id: number;
  strategy_id?: number;
  status?: string;
  created_at?: string;
  metrics_json?: Record<string, unknown>;
};

type BacktestStats = {
  total_return_pct?: number;
  sharpe_ratio?: number;
  max_drawdown_pct?: number;
  win_rate_pct?: number;
  total_trades?: number;
  [key: string]: unknown;
};

type EquityPoint = {
  timestamp: string;
  equity: number;
};

type DrawdownPoint = {
  timestamp: string;
  drawdown_pct: number;
};

type Trade = {
  id?: number;
  symbol?: string;
  side?: string;
  qty?: number;
  price?: number;
  pnl?: number;
  opened_at?: string;
  closed_at?: string;
  [key: string]: unknown;
};

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return res.json();
}

export function useBacktests() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [stats, setStats] = useState<BacktestStats | null>(null);

  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [drawdownCurve, setDrawdownCurve] = useState<DrawdownPoint[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);

  const selectedRun = useMemo(
    () => runs.find((r) => r.id === selectedRunId) ?? null,
    [runs, selectedRunId]
  );

  const loadRunsAndStats = useCallback(async () => {
    const [runsRes, statsRes] = await Promise.all([
      fetchJson<BacktestRun[]>("/quant/backtests"),
      fetchJson<BacktestStats>("/quant/backtests/stats"),
    ]);

    setRuns(runsRes);
    setStats(statsRes);

    if (!selectedRunId && runsRes.length > 0) {
      setSelectedRunId(runsRes[0].id);
    }
  }, [selectedRunId]);

  const loadRunDetail = useCallback(async (runId: number) => {
    const detail = await fetchJson<{
      equity_curve?: EquityPoint[];
      drawdown_curve?: DrawdownPoint[];
      trades?: Trade[];
    }>(`/quant/backtests/${runId}`);

    setEquityCurve(detail.equity_curve ?? []);
    setDrawdownCurve(detail.drawdown_curve ?? []);
    setTrades(detail.trades ?? []);
  }, []);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      await loadRunsAndStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load backtests");
    } finally {
      setLoading(false);
    }
  }, [loadRunsAndStats]);

  const selectRun = useCallback(
    async (run: BacktestRun | number) => {
      const runId = typeof run === "number" ? run : run.id;
      setSelectedRunId(runId);

      try {
        await loadRunDetail(runId);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load run detail");
      }
    },
    [loadRunDetail]
  );

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (selectedRunId != null) {
      void loadRunDetail(selectedRunId).catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load selected run");
      });
    }
  }, [selectedRunId, loadRunDetail]);

  return {
    loading,
    error,

    runs,
    stats,

    selectedRun,
    selectedRunId,
    selectRun,

    equityCurve,
    drawdownCurve,
    trades,

    refreshAll,
  };
}