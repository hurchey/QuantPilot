"use client";

import { useEffect, useMemo, useState } from "react";

import MetricCard from "@/components/ui/MetricCard";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import EmptyState from "@/components/ui/EmptyState";

import EquityCurveChart from "@/components/charts/EquityCurveChart";
import DrawdownChart from "@/components/charts/DrawdownChart";

import BacktestRunsTable from "@/components/tables/BacktestRunsTable";
import TradesTable from "@/components/tables/TradesTable";

import { apiFetch } from "@/lib/api";

/**
 * NOTE:
 * - This file intentionally normalizes a lot of possible backend shapes
 *   so it works even if your API response keys differ slightly.
 * - It also uses your API helper, so requests go to FastAPI (localhost:8000),
 *   not Next.js routes.
 */

type Strategy = {
  id: number | string;
  name: string;
  description?: string | null;
};

type EquityPoint = {
  x: string | number;
  y: number;
};

type DrawdownPoint = {
  x: string | number;
  y: number;
};

type Trade = {
  id: number | string;
  symbol?: string;
  side?: string;
  entry_time?: string | null;
  exit_time?: string | null;
  entry_price?: number | null;
  exit_price?: number | null;
  quantity?: number | null;
  pnl?: number | null;
  return_pct?: number | null;
};

type BacktestRun = {
  id: number | string;
  strategy_id?: number | string | null;
  strategy_name?: string | null;
  name?: string | null;
  symbol?: string | null;
  timeframe?: string | null;
  status?: string | null;
  created_at?: string | null;

  // Metrics (can be top-level or nested in `metrics`)
  total_pnl?: number | null;
  sharpe_ratio?: number | null;
  win_rate?: number | null;
  max_drawdown?: number | null;
  total_trades?: number | null;

  metrics?: Record<string, unknown> | null;

  // Optional detail payloads
  equity_curve?: EquityPoint[] | null;
  drawdown_curve?: DrawdownPoint[] | null;
  trades?: Trade[] | null;
};

type RunDetailState = {
  equityCurve: EquityPoint[];
  drawdownCurve: DrawdownPoint[];
  trades: Trade[];
};

function toArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function toNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return fallback;
}

function toStr(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function pickNumber(obj: Record<string, unknown> | null | undefined, keys: string[], fallback = 0): number {
  if (!obj) return fallback;
  for (const key of keys) {
    if (key in obj) return toNumber(obj[key], fallback);
  }
  return fallback;
}

function pickString(obj: Record<string, unknown> | null | undefined, keys: string[], fallback = ""): string {
  if (!obj) return fallback;
  for (const key of keys) {
    if (key in obj && typeof obj[key] === "string") return obj[key] as string;
  }
  return fallback;
}

function normalizeEquityCurve(raw: unknown): EquityPoint[] {
  const arr = toArray<Record<string, unknown>>(raw);
  return arr
    .map((p, i) => {
      const x =
        (p.timestamp as string) ??
        (p.time as string) ??
        (p.date as string) ??
        (p.x as string) ??
        i;
      const y = toNumber(
        p.equity ?? p.value ?? p.balance ?? p.y ?? p.portfolio_value,
        NaN
      );
      return { x, y };
    })
    .filter((p) => Number.isFinite(p.y));
}

function normalizeDrawdownCurve(raw: unknown): DrawdownPoint[] {
  const arr = toArray<Record<string, unknown>>(raw);
  return arr
    .map((p, i) => {
      const x =
        (p.timestamp as string) ??
        (p.time as string) ??
        (p.date as string) ??
        (p.x as string) ??
        i;
      const y = toNumber(
        p.drawdown ?? p.dd ?? p.value ?? p.y,
        NaN
      );
      return { x, y };
    })
    .filter((p) => Number.isFinite(p.y));
}

function normalizeTrades(raw: unknown): Trade[] {
  const arr = toArray<Record<string, unknown>>(raw);
  return arr.map((t, idx) => ({
    id: (t.id as string | number) ?? idx,
    symbol: toStr(t.symbol ?? t.ticker ?? t.asset, ""),
    side: toStr(t.side ?? t.direction, ""),
    entry_time: toStr(t.entry_time ?? t.entryTime ?? t.open_time ?? t.opened_at, ""),
    exit_time: toStr(t.exit_time ?? t.exitTime ?? t.close_time ?? t.closed_at, ""),
    entry_price: toNumber(t.entry_price ?? t.entryPrice ?? t.open_price, 0),
    exit_price: toNumber(t.exit_price ?? t.exitPrice ?? t.close_price, 0),
    quantity: toNumber(t.quantity ?? t.qty ?? t.size, 0),
    pnl: toNumber(t.pnl ?? t.profit_loss ?? t.profit, 0),
    return_pct: toNumber(t.return_pct ?? t.returnPct ?? t.pnl_pct ?? t.returns, 0),
  }));
}

function normalizeRuns(raw: unknown): BacktestRun[] {
  const arr = toArray<Record<string, unknown>>(raw);

  return arr.map((r, idx) => {
    const metrics = (r.metrics && typeof r.metrics === "object" ? (r.metrics as Record<string, unknown>) : null);

    return {
      id: (r.id as string | number) ?? idx,
      strategy_id: (r.strategy_id as string | number) ?? (r.strategyId as string | number) ?? null,
      strategy_name: pickString(r, ["strategy_name", "strategyName", "name"], ""),
      name: pickString(r, ["name", "run_name", "runName"], ""),
      symbol: pickString(r, ["symbol", "ticker"], ""),
      timeframe: pickString(r, ["timeframe", "interval"], ""),
      status: pickString(r, ["status"], ""),
      created_at: pickString(r, ["created_at", "createdAt", "timestamp"], ""),
      total_pnl: toNumber(r.total_pnl ?? r.totalPnl ?? metrics?.total_pnl ?? metrics?.totalPnl, 0),
      sharpe_ratio: toNumber(r.sharpe_ratio ?? r.sharpe ?? metrics?.sharpe_ratio ?? metrics?.sharpe, 0),
      win_rate: toNumber(r.win_rate ?? r.winRate ?? metrics?.win_rate ?? metrics?.winRate, 0),
      max_drawdown: toNumber(r.max_drawdown ?? r.maxDrawdown ?? metrics?.max_drawdown ?? metrics?.maxDrawdown, 0),
      total_trades: toNumber(r.total_trades ?? r.totalTrades ?? metrics?.total_trades ?? metrics?.totalTrades, 0),
      metrics,
      equity_curve: normalizeEquityCurve(r.equity_curve ?? r.equityCurve ?? metrics?.equity_curve),
      drawdown_curve: normalizeDrawdownCurve(r.drawdown_curve ?? r.drawdownCurve ?? metrics?.drawdown_curve),
      trades: normalizeTrades(r.trades),
    };
  });
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPct(value: number): string {
  return `${value.toFixed(2)}%`;
}

function formatDecimal(value: number): string {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
}

function inferWinRateFromTrades(trades: Trade[]): number {
  if (!trades.length) return 0;
  const wins = trades.filter((t) => (t.pnl ?? 0) > 0).length;
  return (wins / trades.length) * 100;
}

function inferTotalPnlFromTrades(trades: Trade[]): number {
  return trades.reduce((sum, t) => sum + toNumber(t.pnl, 0), 0);
}

function inferMaxDrawdownFromCurve(drawdownCurve: DrawdownPoint[]): number {
  if (!drawdownCurve.length) return 0;
  // Handles drawdown values as negative percentages (e.g., -12.3) or decimals (-0.123)
  const values = drawdownCurve.map((p) => p.y);
  const minVal = Math.min(...values);
  // If values look decimal-based, convert to percent
  if (Math.abs(minVal) <= 1) return minVal * 100;
  return minVal;
}

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | number | null>(null);

  const [runDetail, setRunDetail] = useState<RunDetailState>({
    equityCurve: [],
    drawdownCurve: [],
    trades: [],
  });

  // Cast to "any" so this page works even if your component prop types differ slightly.
  const MetricCardAny = MetricCard as any;
  const ErrorBannerAny = ErrorBanner as any;
  const LoadingSpinnerAny = LoadingSpinner as any;
  const EmptyStateAny = EmptyState as any;
  const EquityCurveChartAny = EquityCurveChart as any;
  const DrawdownChartAny = DrawdownChart as any;
  const BacktestRunsTableAny = BacktestRunsTable as any;
  const TradesTableAny = TradesTable as any;

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      setLoading(true);
      setError(null);

      try {
        const [strategiesRes, runsRes] = await Promise.all([
          apiFetch<unknown>("/quant/strategies"),
          apiFetch<unknown>("/quant/backtests"),
        ]);

        if (!mounted) return;

        const normalizedStrategies = toArray<Record<string, unknown>>(strategiesRes).map((s, idx) => ({
          id: (s.id as string | number) ?? idx,
          name: toStr(s.name ?? s.strategy_name, `Strategy ${idx + 1}`),
          description: toStr(s.description, ""),
        }));

        const normalizedRuns = normalizeRuns(runsRes);

        setStrategies(normalizedStrategies);
        setRuns(normalizedRuns);

        // auto-select latest run
        if (normalizedRuns.length > 0) {
          setSelectedRunId(normalizedRuns[0].id);
        } else {
          setSelectedRunId(null);
          setRunDetail({ equityCurve: [], drawdownCurve: [], trades: [] });
        }
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "Failed to load dashboard data.");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadSelectedRunDetails() {
      if (selectedRunId == null) {
        setRunDetail({ equityCurve: [], drawdownCurve: [], trades: [] });
        return;
      }

      const selectedRun = runs.find((r) => String(r.id) === String(selectedRunId));

      // Seed from run list if already available
      setRunDetail({
        equityCurve: selectedRun?.equity_curve ?? [],
        drawdownCurve: selectedRun?.drawdown_curve ?? [],
        trades: selectedRun?.trades ?? [],
      });

      setDetailLoading(true);

      try {
        // Try common detail/trades endpoints. If one is missing, continue gracefully.
        const detailPromise = apiFetch<unknown>(`/quant/backtests/${selectedRunId}`).catch(() => null);
        const tradesPromise = apiFetch<unknown>(`/quant/backtests/${selectedRunId}/trades`).catch(() => null);

        const [detailRes, tradesRes] = await Promise.all([detailPromise, tradesPromise]);

        if (!mounted) return;

        const detailObj =
          detailRes && typeof detailRes === "object"
            ? (detailRes as Record<string, unknown>)
            : null;

        const nestedResult =
          detailObj?.result && typeof detailObj.result === "object"
            ? (detailObj.result as Record<string, unknown>)
            : null;

        const equityRaw =
          detailObj?.equity_curve ??
          detailObj?.equityCurve ??
          nestedResult?.equity_curve ??
          nestedResult?.equityCurve ??
          detailObj?.metrics;

        const drawdownRaw =
          detailObj?.drawdown_curve ??
          detailObj?.drawdownCurve ??
          nestedResult?.drawdown_curve ??
          nestedResult?.drawdownCurve ??
          detailObj?.metrics;

        const tradesRaw =
          tradesRes ??
          detailObj?.trades ??
          nestedResult?.trades ??
          [];

        setRunDetail({
          equityCurve: normalizeEquityCurve(equityRaw),
          drawdownCurve: normalizeDrawdownCurve(drawdownRaw),
          trades: normalizeTrades(tradesRaw),
        });
      } catch {
        // Keep seeded data if detail fetch fails.
      } finally {
        if (mounted) setDetailLoading(false);
      }
    }

    loadSelectedRunDetails();

    return () => {
      mounted = false;
    };
  }, [selectedRunId, runs]);

  const selectedRun = useMemo(
    () => runs.find((r) => String(r.id) === String(selectedRunId)) ?? null,
    [runs, selectedRunId]
  );

  const dashboardMetrics = useMemo(() => {
    const trades = runDetail.trades;
    const metrics = (selectedRun?.metrics as Record<string, unknown> | null) ?? null;

    const totalPnl =
      selectedRun?.total_pnl ??
      pickNumber(metrics, ["total_pnl", "totalPnl"], inferTotalPnlFromTrades(trades));

    const winRate =
      selectedRun?.win_rate ??
      pickNumber(metrics, ["win_rate", "winRate"], inferWinRateFromTrades(trades));

    const sharpe =
      selectedRun?.sharpe_ratio ??
      pickNumber(metrics, ["sharpe_ratio", "sharpe"], 0);

    const maxDrawdown =
      selectedRun?.max_drawdown ??
      pickNumber(metrics, ["max_drawdown", "maxDrawdown"], inferMaxDrawdownFromCurve(runDetail.drawdownCurve));

    const totalTrades =
      selectedRun?.total_trades ??
      pickNumber(metrics, ["total_trades", "totalTrades"], trades.length);

    return {
      totalStrategies: strategies.length,
      totalRuns: runs.length,
      totalTrades,
      totalPnl,
      winRate,
      sharpe,
      maxDrawdown,
    };
  }, [selectedRun, runDetail, runs.length, strategies.length]);

  if (loading) {
    return (
      <div className="py-16">
        <LoadingSpinnerAny label="Loading dashboard..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error ? (
        <ErrorBannerAny
          message={error}
          error={error}
          title="Dashboard Error"
        />
      ) : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-slate-400">
            QuantPilot overview for strategies, backtests, and trade performance.
          </p>
        </div>

        {selectedRun ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-3 py-2 text-xs text-slate-300">
            <div>
              <span className="text-slate-400">Selected Run:</span>{" "}
              <span className="font-medium text-slate-100">
                {selectedRun.name || selectedRun.strategy_name || `Run #${selectedRun.id}`}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-3 text-slate-400">
              {selectedRun.symbol ? <span>Symbol: {selectedRun.symbol}</span> : null}
              {selectedRun.timeframe ? <span>Timeframe: {selectedRun.timeframe}</span> : null}
              {selectedRun.status ? <span>Status: {selectedRun.status}</span> : null}
            </div>
          </div>
        ) : null}
      </div>

      {runs.length === 0 ? (
        <EmptyStateAny
          title="No backtests yet"
          heading="No backtests yet"
          description="Create a strategy and run your first backtest to populate the dashboard."
          body="Create a strategy and run your first backtest to populate the dashboard."
        />
      ) : (
        <>
          {/* Metrics */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCardAny
              title="Total Strategies"
              label="Total Strategies"
              value={String(dashboardMetrics.totalStrategies)}
              subtitle="Configured strategies"
              hint="Configured strategies"
            />
            <MetricCardAny
              title="Backtest Runs"
              label="Backtest Runs"
              value={String(dashboardMetrics.totalRuns)}
              subtitle="Historical runs"
              hint="Historical runs"
            />
            <MetricCardAny
              title="Total PnL"
              label="Total PnL"
              value={formatCurrency(dashboardMetrics.totalPnl)}
              subtitle="Selected run"
              hint="Selected run"
            />
            <MetricCardAny
              title="Win Rate"
              label="Win Rate"
              value={formatPct(dashboardMetrics.winRate)}
              subtitle="Selected run"
              hint="Selected run"
            />
            <MetricCardAny
              title="Sharpe Ratio"
              label="Sharpe Ratio"
              value={formatDecimal(dashboardMetrics.sharpe)}
              subtitle="Risk-adjusted return"
              hint="Risk-adjusted return"
            />
            <MetricCardAny
              title="Max Drawdown"
              label="Max Drawdown"
              value={formatPct(dashboardMetrics.maxDrawdown)}
              subtitle="Selected run"
              hint="Selected run"
            />
            <MetricCardAny
              title="Trades"
              label="Trades"
              value={String(dashboardMetrics.totalTrades)}
              subtitle="Selected run"
              hint="Selected run"
            />
            <MetricCardAny
              title="Detail Status"
              label="Detail Status"
              value={detailLoading ? "Syncing..." : "Ready"}
              subtitle="Run detail fetch"
              hint="Run detail fetch"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-slate-200">Equity Curve</h2>
                <span className="text-xs text-slate-400">
                  {runDetail.equityCurve.length} points
                </span>
              </div>

              {runDetail.equityCurve.length > 0 ? (
                <EquityCurveChartAny
                  data={runDetail.equityCurve}
                  points={runDetail.equityCurve}
                />
              ) : (
                <EmptyStateAny
                  title="No equity curve"
                  heading="No equity curve"
                  description="Run details did not include an equity curve for this backtest."
                  compact
                />
              )}
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-slate-200">Drawdown Curve</h2>
                <span className="text-xs text-slate-400">
                  {runDetail.drawdownCurve.length} points
                </span>
              </div>

              {runDetail.drawdownCurve.length > 0 ? (
                <DrawdownChartAny
                  data={runDetail.drawdownCurve}
                  points={runDetail.drawdownCurve}
                />
              ) : (
                <EmptyStateAny
                  title="No drawdown curve"
                  heading="No drawdown curve"
                  description="Run details did not include a drawdown curve for this backtest."
                  compact
                />
              )}
            </div>
          </div>

          {/* Tables */}
          <div className="grid grid-cols-1 gap-6 2xl:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-slate-200">Backtest Runs</h2>
                <span className="text-xs text-slate-400">{runs.length} total</span>
              </div>

              <BacktestRunsTableAny
                runs={runs}
                data={runs}
                selectedRunId={selectedRunId}
                selectedId={selectedRunId}
                onSelectRunAction={(id: string | number) => setSelectedRunId(id)}
                onSelectRun={(id: string | number) => setSelectedRunId(id)}
              />
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-medium text-slate-200">Trades</h2>
                <span className="text-xs text-slate-400">
                  {runDetail.trades.length} in selected run
                </span>
              </div>

              <TradesTableAny
                trades={runDetail.trades}
                data={runDetail.trades}
                rows={runDetail.trades}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}