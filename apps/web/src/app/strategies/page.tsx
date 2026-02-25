"use client";

import { useEffect, useState } from "react";

import StrategyForm from "@/components/strategies/StrategyForm";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import EmptyState from "@/components/ui/EmptyState";
import MetricCard from "@/components/ui/MetricCard";

import { apiFetch } from "@/lib/api";

type Strategy = {
  id: number | string;
  name: string;
  description?: string | null;
  symbol?: string | null;
  timeframe?: string | null;
  created_at?: string | null;
};

function toArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export default function StrategiesPage() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const StrategyFormAny = StrategyForm as any;
  const ErrorBannerAny = ErrorBanner as any;
  const LoadingSpinnerAny = LoadingSpinner as any;
  const EmptyStateAny = EmptyState as any;
  const MetricCardAny = MetricCard as any;

  async function loadStrategies(showSpinner = true) {
    if (showSpinner) setLoading(true);
    else setRefreshing(true);

    setError(null);

    try {
      const res = await apiFetch<unknown>("/quant/strategies");
      const rows = toArray<Record<string, unknown>>(res);

      const normalized = rows.map((s, idx) => ({
        id: (s.id as number | string) ?? idx,
        name: String(s.name ?? s.strategy_name ?? `Strategy ${idx + 1}`),
        description: s.description ? String(s.description) : "",
        symbol: s.symbol ? String(s.symbol) : "",
        timeframe: s.timeframe ? String(s.timeframe) : "",
        created_at: s.created_at ? String(s.created_at) : "",
      }));

      setStrategies(normalized);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load strategies.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadStrategies(true);
  }, []);

  const handleStrategyCreated = async () => {
    await loadStrategies(false);
  };

  return (
    <div className="space-y-6">
      {error ? <ErrorBannerAny title="Strategies Error" message={error} error={error} /> : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Strategies</h1>
          <p className="text-sm text-slate-400">
            Create and manage quant strategies used for backtesting.
          </p>
        </div>

        <button
          onClick={() => loadStrategies(false)}
          className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm hover:bg-slate-800"
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCardAny title="Strategies" value={String(strategies.length)} subtitle="Configured" />
        <MetricCardAny
          title="With Symbols"
          value={String(strategies.filter((s) => s.symbol).length)}
          subtitle="Ready for runs"
        />
        <MetricCardAny
          title="With Timeframes"
          value={String(strategies.filter((s) => s.timeframe).length)}
          subtitle="Configured timeframe"
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Create Strategy</h2>

        <StrategyFormAny
          onCreated={handleStrategyCreated}
          onCreatedAction={handleStrategyCreated}
          onSuccess={handleStrategyCreated}
          onSuccessAction={handleStrategyCreated}
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Saved Strategies</h2>

        {loading ? (
          <LoadingSpinnerAny label="Loading strategies..." />
        ) : strategies.length === 0 ? (
          <EmptyStateAny
            title="No strategies yet"
            description="Create your first quant strategy above to get started."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-slate-400">
                <tr className="border-b border-slate-800">
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Symbol</th>
                  <th className="px-3 py-2">Timeframe</th>
                  <th className="px-3 py-2">Description</th>
                </tr>
              </thead>
              <tbody>
                {strategies.map((s) => (
                  <tr key={String(s.id)} className="border-b border-slate-800/60">
                    <td className="px-3 py-2 font-medium text-slate-100">{s.name}</td>
                    <td className="px-3 py-2 text-slate-300">{s.symbol || "—"}</td>
                    <td className="px-3 py-2 text-slate-300">{s.timeframe || "—"}</td>
                    <td className="px-3 py-2 text-slate-400">{s.description || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}