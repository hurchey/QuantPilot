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

type Strategy = {
  id: number | string;
  name: string;
};

type BacktestRun = {
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

type Trade = {
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
  const [trades, setTrades] = useState<Trade[]>([]);
  const [tradesLoading, setTradesLoading] = useState(false);

  const [form, setForm] = useState({
    strategy_id: "",
    symbol: "AAPL",
    timeframe: "1D",
    initial_cash: "100000",
    commission_bps: "1",
  });

  const BacktestRunsTableAny = BacktestRunsTable as any;
  const TradesTableAny = TradesTable as any;
  const ErrorBannerAny = ErrorBanner as any;
  const LoadingSpinnerAny = LoadingSpinner as any;
  const EmptyStateAny = EmptyState as any;
  const MetricCardAny = MetricCard as any;

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
      }));

      const runRows = toArray<Record<string, unknown>>(runsRes).map((r, idx) => ({
        id: (r.id as string | number) ?? idx,
        strategy_name: String(r.strategy_name ?? r.strategyName ?? r.name ?? ""),
        symbol: String(r.symbol ?? ""),
        timeframe: String(r.timeframe ?? ""),
        status: String(r.status ?? ""),
        created_at: String(r.created_at ?? ""),
        total_pnl: toNum(r.total_pnl ?? r.totalPnl ?? (r as any)?.metrics?.total_pnl, 0),
        sharpe_ratio: toNum(r.sharpe_ratio ?? r.sharpe ?? (r as any)?.metrics?.sharpe, 0),
        win_rate: toNum(r.win_rate ?? r.winRate ?? (r as any)?.metrics?.win_rate, 0),
        max_drawdown: toNum(r.max_drawdown ?? r.maxDrawdown ?? (r as any)?.metrics?.max_drawdown, 0),
        total_trades: toNum(r.total_trades ?? r.totalTrades ?? (r as any)?.metrics?.total_trades, 0),
      }));

      setStrategies(strategyRows);
      setRuns(runRows);

      if (!form.strategy_id && strategyRows.length > 0) {
        setForm((prev) => ({ ...prev, strategy_id: String(strategyRows[0].id) }));
      }

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

    async function loadTrades() {
      if (selectedRunId == null) {
        setTrades([]);
        return;
      }

      setTradesLoading(true);
      try {
        const res = await apiFetch<unknown>(`/quant/backtests/${selectedRunId}/trades`);
        const rows = toArray<Record<string, unknown>>(res).map((t, idx) => ({
          id: (t.id as string | number) ?? idx,
          symbol: String(t.symbol ?? ""),
          side: String(t.side ?? t.direction ?? ""),
          entry_time: String(t.entry_time ?? t.entryTime ?? ""),
          exit_time: String(t.exit_time ?? t.exitTime ?? ""),
          entry_price: toNum(t.entry_price ?? t.entryPrice, 0),
          exit_price: toNum(t.exit_price ?? t.exitPrice, 0),
          quantity: toNum(t.quantity ?? t.qty, 0),
          pnl: toNum(t.pnl ?? 0, 0),
          return_pct: toNum(t.return_pct ?? t.returnPct ?? 0, 0),
        }));

        if (active) setTrades(rows);
      } catch {
        if (active) setTrades([]);
      } finally {
        if (active) setTradesLoading(false);
      }
    }

    loadTrades();
    return () => {
      active = false;
    };
  }, [selectedRunId]);

  const selectedRun = useMemo(
    () => runs.find((r) => String(r.id) === String(selectedRunId)) ?? null,
    [runs, selectedRunId]
  );

  async function handleRunBacktest(e: FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);

    const payload = {
      strategy_id: Number(form.strategy_id),
      initial_capital: Number(form.initial_cash),
      fees_bps: Number(form.commission_bps),
      slippage_bps: 1,
    };

    try {
      await apiFetch("/quant/backtests/run", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      await loadPage();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run backtest.");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return (
      <div className="py-16">
        <LoadingSpinnerAny label="Loading backtests..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error ? <ErrorBannerAny title="Backtests Error" message={error} error={error} /> : null}

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Backtests</h1>
        <p className="text-sm text-slate-400">
          Run strategy simulations and inspect execution-level trade results.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCardAny title="Runs" value={String(runs.length)} subtitle="Historical runs" />
        <MetricCardAny title="Trades" value={String(trades.length)} subtitle="Selected run" />
        <MetricCardAny
          title="Sharpe"
          value={selectedRun ? (selectedRun.sharpe_ratio ?? 0).toFixed(2) : "0.00"}
          subtitle="Selected run"
        />
        <MetricCardAny
          title="PnL"
          value={selectedRun ? `$${(selectedRun.total_pnl ?? 0).toFixed(2)}` : "$0.00"}
          subtitle="Selected run"
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Run New Backtest</h2>

        <form onSubmit={handleRunBacktest} className="grid grid-cols-1 gap-3 md:grid-cols-6">
          <div className="md:col-span-2">
            <label className="mb-1 block text-xs text-slate-400">Strategy</label>
            <select
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.strategy_id}
              onChange={(e) => setForm((p) => ({ ...p, strategy_id: e.target.value }))}
              required
            >
              <option value="">
                {strategies.length === 0
                  ? "No strategies—create one first"
                  : "Select strategy"}
              </option>
              {strategies.map((s) => (
                <option key={String(s.id)} value={String(s.id)}>
                  {s.name}
                </option>
              ))}
            </select>
            {strategies.length === 0 && (
              <p className="mt-1 text-xs text-slate-500">
                <Link href="/strategies" className="text-blue-400 hover:underline">
                  Create a strategy
                </Link>{" "}
                on the Strategies page to run backtests.
              </p>
            )}
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
          </div>

          <div>
            <label className="mb-1 block text-xs text-slate-400">Timeframe</label>
            <input
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={form.timeframe}
              onChange={(e) => setForm((p) => ({ ...p, timeframe: e.target.value }))}
              placeholder="1D"
              required
            />
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

          <div className="md:col-span-6">
            <button
              type="submit"
              disabled={running || strategies.length === 0}
              className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60"
            >
              {running ? "Running backtest..." : strategies.length === 0 ? "Create a strategy first" : "Run Backtest"}
            </button>
          </div>
        </form>
      </div>

      {runs.length === 0 ? (
        <EmptyStateAny
          title="No backtest runs yet"
          description="Create a strategy, upload data, then run your first backtest."
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 2xl:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <h2 className="mb-3 text-sm font-medium text-slate-200">Backtest Runs</h2>
            <BacktestRunsTableAny
              runs={runs}
              data={runs}
              selectedRunId={selectedRunId}
              selectedId={selectedRunId}
              onSelectRun={(id: string | number) => setSelectedRunId(id)}
              onSelectRunAction={(id: string | number) => setSelectedRunId(id)}
            />
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <h2 className="mb-3 text-sm font-medium text-slate-200">Trades</h2>
            {tradesLoading ? (
              <LoadingSpinnerAny label="Loading trades..." />
            ) : (
              <TradesTableAny trades={trades} data={trades} rows={trades} />
            )}
          </div>
        </div>
      )}
    </div>
  );
}