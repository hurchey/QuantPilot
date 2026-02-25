"use client";

import React, { useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { apiFetch } from "@/lib/api";

type DemoDataFormProps = {
  onSuccess?: () => void;
  className?: string;
};

export default function DemoDataForm({ onSuccess, className = "" }: DemoDataFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [symbol, setSymbol] = useState("SPY");
  const [numDays, setNumDays] = useState(252);

  async function handleLoadDemo() {
    setError("");
    setSuccessMessage("");
    setLoading(true);

    try {
      const res = await apiFetch<{ rows_inserted: number; symbol: string; timeframe: string }>(
        "/quant/data/load-demo",
        {
          method: "POST",
          body: JSON.stringify({ symbol, timeframe: "1d", num_days: numDays }),
        }
      );
      const rows = res?.rows_inserted ?? 0;
      setSuccessMessage(
        `Loaded ${rows} bars of ${res?.symbol ?? symbol} (1d). You can now create strategies and run backtests.`
      );
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo data");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <p className="text-sm text-slate-400">
        Load synthetic OHLCV data instantly—no file upload. Perfect for trying the app.
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
          <label className="mb-1 block text-sm text-slate-300">Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="SPY"
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-300">Trading days</label>
          <input
            type="number"
            value={numDays}
            onChange={(e) => setNumDays(Math.max(10, Math.min(1000, Number(e.target.value) || 252)))}
            min={10}
            max={1000}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={handleLoadDemo}
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
      >
        {loading ? (
          <>
            <LoadingSpinner size="sm" />
            Loading...
          </>
        ) : (
          "Load demo data"
        )}
      </button>
    </div>
  );
}
