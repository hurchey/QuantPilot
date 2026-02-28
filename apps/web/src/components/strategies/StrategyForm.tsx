"use client";

import React, { useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { apiFetch } from "@/lib/api";
import { STRATEGY_TYPES, TIMEFRAME_OPTIONS } from "@/lib/constants";

type StrategyFormProps = {
  onCreated?: () => void;
  onCreatedAction?: () => void;
  onSuccess?: () => void;
  onSuccessAction?: () => void;
  className?: string;
};

export default function StrategyForm({
  onCreated,
  onCreatedAction,
  onSuccess,
  onSuccessAction,
  className = "",
}: StrategyFormProps) {
  const [name, setName] = useState("");
  const [strategyType, setStrategyType] = useState<string>(STRATEGY_TYPES[0]?.value ?? "sma_crossover");
  const [symbol, setSymbol] = useState("SPY");
  const [timeframe, setTimeframe] = useState("1d");
  const [fastWindow, setFastWindow] = useState("10");
  const [slowWindow, setSlowWindow] = useState("20");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSuccess = () => {
    onCreated?.();
    onCreatedAction?.();
    onSuccess?.();
    onSuccessAction?.();
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    const parameters_json: Record<string, unknown> = {};
    if (strategyType === "sma_crossover") {
      parameters_json.fast_window = Number(fastWindow) || 10;
      parameters_json.slow_window = Number(slowWindow) || 20;
    }

    setLoading(true);
    try {
        const strategyLabel = STRATEGY_TYPES.find((t) => t.value === strategyType)?.label ?? strategyType;
        await apiFetch("/quant/strategies", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim() || `${strategyLabel} - ${symbol}`,
          strategy_type: strategyType,
          symbol: symbol.trim().toUpperCase(),
          timeframe: timeframe.trim(),
          parameters_json,
        }),
      });

      setSuccessMessage("Strategy created successfully.");
      setName("");
      setFastWindow("10");
      setSlowWindow("20");
      handleSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create strategy");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={`qp-panel space-y-4 ${className}`}>
      <div className="qp-panel-header">
        <h2>Create Strategy</h2>
      </div>

      <p className="text-sm text-slate-400">
        Define a trading strategy with symbol, timeframe, and parameters for backtesting.
      </p>

      {error ? (
        <ErrorBanner title="Error" message={error} onDismissAction={() => setError("")} />
      ) : null}

      {successMessage ? (
        <div className="rounded-xl border border-emerald-800/70 bg-emerald-950/20 px-4 py-3 text-sm text-emerald-200">
          {successMessage}
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm text-slate-300">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. SPY SMA 10/20"
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-slate-300">Strategy type</label>
          <select
            value={strategyType}
            onChange={(e) => setStrategyType(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          >
            {STRATEGY_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-sm text-slate-300">Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="SPY"
            required
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-slate-300">Timeframe</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          >
            {TIMEFRAME_OPTIONS.map((tf) => (
              <option key={tf} value={tf}>
                {tf}
              </option>
            ))}
          </select>
        </div>

        {strategyType === "sma_crossover" && (
          <>
            <div>
              <label className="mb-1 block text-sm text-slate-300">Fast window</label>
              <input
                type="number"
                value={fastWindow}
                onChange={(e) => setFastWindow(e.target.value)}
                min={1}
                max={200}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm text-slate-300">Slow window</label>
              <input
                type="number"
                value={slowWindow}
                onChange={(e) => setSlowWindow(e.target.value)}
                min={1}
                max={200}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
              />
            </div>
          </>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button type="submit" className="qp-btn qp-btn-primary" disabled={loading}>
          {loading ? "Creating..." : "Create Strategy"}
        </button>
        {loading ? <LoadingSpinner size="sm" text="Creating..." /> : null}
      </div>
    </form>
  );
}
