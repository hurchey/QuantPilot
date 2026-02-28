"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import BacktestRunsTable from "@/components/tables/BacktestRunsTable";
import TradesTable from "@/components/tables/TradesTable";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import EmptyState from "@/components/ui/EmptyState";
import MetricCard from "@/components/ui/MetricCard";

import { apiFetch } from "@/lib/api";
import { STRATEGY_TYPES, TIMEFRAME_OPTIONS } from "@/lib/constants";

type Strategy = {
  id: number | string;
  name: string;
  strategy_type?: string;
  symbol?: string;
  timeframe?: string;
};

type BacktestRun = {
  id: number | string;
  strategy_id?: number;
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
  metrics_json?: Record<string, unknown>;
};

type RoundTrip = {
  entry_ts: string;
  exit_ts: string;
  entry_price: number;
  exit_price: number;
  qty: number;
  realized_pnl: number;
  win: boolean;
  attribution: string;
  holding_bars: number;
  price_return_pct: number;
};

type TradeAnalysis = {
  summary: {
    num_wins: number;
    num_losses: number;
    win_rate: number;
    win_attribution: Record<string, number>;
    loss_attribution: Record<string, number>;
    insight: string;
  };
  round_trips: RoundTrip[];
};

function toArray<T = unknown>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object" && "strategies" in value) {
    const s = (value as Record<string, unknown>).strategies;
    return Array.isArray(s) ? (s as T[]) : [];
  }
  if (value && typeof value === "object" && "data" in value) {
    const d = (value as Record<string, unknown>).data;
    return Array.isArray(d) ? (d as T[]) : [];
  }
  return [];
}

function toNum(v: unknown, d = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : d;
}

export default function BacktestsPage() {
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [runs, setRuns] = useState<BacktestRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | number | null>(null);
  const [roundTrips, setRoundTrips] = useState<RoundTrip[]>([]);
  const [tradeAnalysis, setTradeAnalysis] = useState<TradeAnalysis | null>(null);
  const [volatility, setVolatility] = useState<Record<string, unknown> | null>(null);
  const [regime, setRegime] = useState<Record<string, unknown> | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  const [form, setForm] = useState({
    strategy_type: "sma_crossover",
    symbol: "AAPL",
    timeframe: "1d",
    initial_cash: "100000",
    commission_bps: "1",
    slippage_bps: "1",
  });

  const selectedRun = useMemo(
    () => runs.find((r) => String(r.id) === String(selectedRunId)) ?? null,
    [runs, selectedRunId]
  );

  async function loadPage() {
    setLoading(true);
    setError(null);

    try {
      const [strategiesRes, runsRes] = await Promise.all([
        apiFetch<unknown>("/quant/strategies"),
        apiFetch<unknown>("/quant/backtests"),
      ]);

      const strategyRows = toArray<Record<string, unknown>>(strategiesRes).map((s, idx) => ({
        id: (s.id as string | number) ?? idx,
        name: String(s.name ?? s.strategy_name ?? `Strategy ${idx + 1}`),
        strategy_type: String(s.strategy_type ?? "sma_crossover"),
        symbol: String(s.symbol ?? ""),
        timeframe: String(s.timeframe ?? "1d"),
      }));

      const runRows = toArray<Record<string, unknown>>(runsRes).map((r, idx) => ({
        id: (r.id as string | number) ?? idx,
        strategy_id: r.strategy_id != null ? toNum(r.strategy_id) : undefined,
        strategy_name: String(r.strategy_name ?? r.strategyName ?? ""),
        symbol: String(r.symbol ?? ""),
        timeframe: String(r.timeframe ?? ""),
        status: String(r.status ?? ""),
        created_at: String(r.created_at ?? ""),
        metrics_json: (r.metrics_json ?? r) as Record<string, unknown>,
        total_pnl: toNum((r as any)?.metrics_json?.total_return ?? (r as any)?.total_pnl, 0),
        sharpe_ratio: toNum((r as any)?.metrics_json?.sharpe ?? (r as any)?.sharpe_ratio, 0),
        win_rate: toNum((r as any)?.metrics_json?.win_rate ?? (r as any)?.win_rate, 0),
        max_drawdown: toNum((r as any)?.metrics_json?.max_drawdown ?? (r as any)?.max_drawdown, 0),
        total_trades: toNum((r as any)?.metrics_json?.num_trades ?? (r as any)?.total_trades, 0),
      }));

      setStrategies(strategyRows);
      setRuns(runRows);

      if (runRows.length > 0 && selectedRunId == null) {
        setSelectedRunId(runRows[0].id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load backtests page.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPage();
  }, []);

  useEffect(() => {
    let active = true;

    async function loadInsights() {
      if (selectedRunId == null || !selectedRun) {
        setRoundTrips([]);
        setTradeAnalysis(null);
        setVolatility(null);
        setRegime(null);
        return;
      }

      setInsightsLoading(true);
      try {
        const symbol = selectedRun.symbol ?? "";
        const [analysisRes, volRes, regimeRes] = await Promise.allSettled([
          apiFetch<unknown>(`/quant/backtests/${selectedRunId}/trade-analysis`),
          symbol
            ? apiFetch<unknown>(`/quant/backtest-pipeline/volatility/${symbol}`)
            : Promise.reject(new Error("No symbol")),
          symbol
            ? apiFetch<unknown>(`/quant/backtest-pipeline/regime/${symbol}`)
            : Promise.reject(new Error("No symbol")),
        ]);

        if (active) {
          if (analysisRes.status === "fulfilled" && analysisRes.value) {
            const a = analysisRes.value as Record<string, unknown>;
            setRoundTrips((a.round_trips as RoundTrip[]) ?? []);
            setTradeAnalysis({
              summary: a.summary as TradeAnalysis["summary"],
              round_trips: (a.round_trips as RoundTrip[]) ?? [],
            });
          } else {
            setRoundTrips([]);
            setTradeAnalysis(null);
          }
          if (volRes.status === "fulfilled" && volRes.value) {
            setVolatility(volRes.value as Record<string, unknown>);
          } else {
            setVolatility(null);
          }
          if (regimeRes.status === "fulfilled" && regimeRes.value) {
            setRegime(regimeRes.value as Record<string, unknown>);
          } else {
            setRegime(null);
          }
        }
      } catch {
        if (active) {
          setRoundTrips([]);
          setTradeAnalysis(null);
          setVolatility(null);
          setRegime(null);
        }
      } finally {
        if (active) setInsightsLoading(false);
      }
    }

    loadInsights();
  }, [selectedRunId, selectedRun?.symbol]);

  async function handleRunBacktest(e: FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);

    const symbol = form.symbol.trim().toUpperCase();
    if (!symbol) {
      setError("Symbol is required.");
      setRunning(false);
      return;
    }

    try {
      // Find existing strategy with this type + symbol, or create one
      let strategyId = strategies.find(
        (s) => s.strategy_type === form.strategy_type && s.symbol === symbol
      )?.id;

      if (!strategyId) {
        const strategyLabel = STRATEGY_TYPES.find((t) => t.value === form.strategy_type)?.label ?? form.strategy_type;
        const created = await apiFetch<{ id: number }>("/quant/strategies", {
          method: "POST",
          body: JSON.stringify({
            name: `${strategyLabel} - ${symbol}`,
            strategy_type: form.strategy_type,
            symbol,
            timeframe: form.timeframe,
            parameters_json:
              form.strategy_type === "sma_crossover"
                ? { fast_window: 10, slow_window: 30 }
                : {},
          }),
        });
        strategyId = (created as { id: number }).id;
      }

      await apiFetch("/quant/backtests/run", {
        method: "POST",
        body: JSON.stringify({
          strategy_id: Number(strategyId),
          initial_capital: Number(form.initial_cash),
          fees_bps: Number(form.commission_bps),
          slippage_bps: Number(form.slippage_bps),
        }),
      });

      await loadPage();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run backtest.");
    } finally {
      setRunning(false);
    }
  }

  const metrics = selectedRun?.metrics_json ?? {};
  const totalReturn = toNum(metrics.total_return ?? metrics.total_return_pct, 0);
  const sharpe = toNum(metrics.sharpe ?? metrics.sharpe_ratio, 0);
  const winRate = toNum(metrics.win_rate ?? tradeAnalysis?.summary?.win_rate, 0);
  const numTrades = toNum(metrics.num_trades ?? metrics.num_round_trips, 0);

  if (loading) {
    return (
      <div className="py-16">
        <LoadingSpinner text="Loading backtests..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error ? <ErrorBanner title="Backtests Error" message={error} error={error} /> : null}

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Backtests</h1>
        <p className="text-sm text-slate-400">
          Run strategy simulations and inspect execution-level trade results.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard title="Runs" value={String(runs.length)} helperText="Historical runs" />
        <MetricCard
          title="Round trips"
          value={String(roundTrips.length || numTrades)}
          helperText="Selected run"
        />
        <MetricCard
          title="Sharpe"
          value={selectedRun ? sharpe.toFixed(2) : "0.00"}
          helperText="Selected run"
        />
        <MetricCard
          title="Return"
          value={selectedRun ? `${(totalReturn * 100).toFixed(2)}%` : "0%"}
          helperText="Selected run"
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Run New Backtest</h2>

        <form onSubmit={handleRunBacktest} className="grid grid-cols-1 gap-3 md:grid-cols-6">
          <div>
            <label className="mb-1 block text-xs text-slate-400">Strategy</label>
            <select
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.strategy_type}
              onChange={(e) => setForm((p) => ({ ...p, strategy_type: e.target.value }))}
            >
              {STRATEGY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
            <p className="mt-0.5 text-xs text-slate-500">Trading logic to run</p>
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">Symbol</label>
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.symbol}
              onChange={(e) => setForm((p) => ({ ...p, symbol: e.target.value.toUpperCase() }))}
              placeholder="AAPL"
              required
            />
            <p className="mt-0.5 text-xs text-slate-500">Stock ticker to backtest</p>
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">Timeframe</label>
            <select
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.timeframe}
              onChange={(e) => setForm((p) => ({ ...p, timeframe: e.target.value }))}
            >
              {TIMEFRAME_OPTIONS.filter((tf) => ["1d", "1wk", "1m", "5m", "15m", "1h"].includes(tf)).map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">Initial Cash</label>
            <input
              type="number"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.initial_cash}
              onChange={(e) => setForm((p) => ({ ...p, initial_cash: e.target.value }))}
              min={0}
              step="1000"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">Commission (bps)</label>
            <input
              type="number"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.commission_bps}
              onChange={(e) => setForm((p) => ({ ...p, commission_bps: e.target.value }))}
              min={0}
              step="1"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">Slippage (bps)</label>
            <input
              type="number"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.slippage_bps}
              onChange={(e) => setForm((p) => ({ ...p, slippage_bps: e.target.value }))}
              min={0}
              step="1"
            />
          </div>

          <div className="md:col-span-6">
            <button
              type="submit"
              disabled={running}
              className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60"
            >
              {running ? "Running backtest..." : "Run Backtest"}
            </button>
          </div>
        </form>
      </div>

      {runs.length === 0 ? (
        <EmptyState
          title="No backtest runs yet"
          description="Create a strategy, upload data, then run your first backtest."
        />
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 2xl:grid-cols-2">
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h2 className="mb-3 text-sm font-medium text-slate-200">Backtest Runs</h2>
              <BacktestRunsTable
                runs={runs}
                selectedRunId={selectedRunId}
                onSelectRun={(id) => setSelectedRunId(id)}
                onSelectRunAction={(r) => setSelectedRunId(r.id)}
              />
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h2 className="mb-3 text-sm font-medium text-slate-200">Trades (Round Trips)</h2>
              {insightsLoading ? (
                <LoadingSpinner text="Loading trades..." />
              ) : roundTrips.length > 0 ? (
                <TradesTable
                  trades={roundTrips.map((rt, i) => ({
                    id: i,
                    symbol: selectedRun?.symbol,
                    side: "LONG",
                    entry_price: rt.entry_price,
                    exit_price: rt.exit_price,
                    quantity: rt.qty,
                    pnl: rt.realized_pnl,
                    entry_time: rt.entry_ts,
                    exit_time: rt.exit_ts,
                    opened_at: rt.entry_ts,
                    closed_at: rt.exit_ts,
                    win: rt.win,
                    attribution: rt.attribution,
                    price_return_pct: rt.price_return_pct,
                  }))}
                />
              ) : (
                <div className="text-sm text-slate-400">No round-trip trades for this run.</div>
              )}
            </div>
          </div>

          {(volatility || regime || tradeAnalysis) && (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
              <h2 className="mb-3 text-sm font-medium text-slate-200">Insights</h2>
              {insightsLoading ? (
                <LoadingSpinner text="Loading insights..." />
              ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  {volatility && (
                    <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-3">
                      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Volatility</h3>
                      <p className="mt-1 text-sm text-slate-200">
                        {(volatility.annualized_vol as number)?.toFixed(2) ?? "—"} ann. vol
                      </p>
                      <p className="text-xs text-slate-400">
                        Label: {(volatility.volatility_label as string) ?? "—"} (vs avg: {(volatility.vs_average as number)?.toFixed(2) ?? "—"}x)
                      </p>
                    </div>
                  )}
                  {regime && (
                    <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-3">
                      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Regime</h3>
                      <p className="mt-1 text-sm text-slate-200 capitalize">
                        {(regime.regime as string) ?? "—"}
                      </p>
                      <p className="text-xs text-slate-400">
                        Confidence: {((regime.confidence as number) * 100)?.toFixed(0) ?? "—"}%
                      </p>
                    </div>
                  )}
                  {tradeAnalysis?.summary && (
                    <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-3 md:col-span-1">
                      <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Trade Analysis</h3>
                      <p className="mt-1 text-sm text-slate-200">
                        {tradeAnalysis.summary.num_wins} wins / {tradeAnalysis.summary.num_losses} losses
                        ({(tradeAnalysis.summary.win_rate * 100).toFixed(0)}% win rate)
                      </p>
                      <p className="mt-2 text-xs text-slate-400 italic">
                        {tradeAnalysis.summary.insight}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
