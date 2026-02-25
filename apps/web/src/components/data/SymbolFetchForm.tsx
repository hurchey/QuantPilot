"use client";

import React, { useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { apiFetch } from "@/lib/api";

type SymbolFetchFormProps = {
  onSuccess?: () => void;
  className?: string;
};

export default function SymbolFetchForm({ onSuccess, className = "" }: SymbolFetchFormProps) {
  const [symbol, setSymbol] = useState("SPY");
  const [timeframe, setTimeframe] = useState("1d");
  const [days, setDays] = useState(365);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  async function handleFetch() {
    setError("");
    setSuccessMessage("");
    setLoading(true);

    try {
      const res = await apiFetch<{ rows_inserted: number; symbol: string; timeframe: string }>(
        "/quant/data/fetch-symbol",
        {
          method: "POST",
          body: JSON.stringify({ symbol, timeframe, days }),
        }
      );
      setSuccessMessage(
        `Fetched ${res?.rows_inserted ?? 0} bars for ${res?.symbol ?? symbol} (${res?.timeframe ?? timeframe}).`
      );
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Fetch failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <p className="text-sm text-slate-400">
        Fetch historical OHLCV from Yahoo Finance. Real market data for backtesting.
      </p>

      {error ? (
        <ErrorBanner title="Fetch Error" message={error} onDismissAction={() => setError("")} />
      ) : null}
      {successMessage ? (
        <div className="rounded-xl border border-emerald-800/70 bg-emerald-950/20 px-4 py-3 text-sm text-emerald-200">
          {successMessage}
        </div>
      ) : null}

      <div className="grid gap-3 md:grid-cols-3">
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
          <label className="mb-1 block text-sm text-slate-300">Timeframe</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="1d">1d</option>
            <option value="1wk">1wk</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-300">Days</label>
          <input
            type="number"
            value={days}
            onChange={(e) => setDays(Math.max(1, Math.min(3650, Number(e.target.value) || 365)))}
            min={1}
            max={3650}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={handleFetch}
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-100 hover:bg-slate-600 disabled:opacity-50"
      >
        {loading ? (
          <>
            <LoadingSpinner size="sm" />
            Fetching...
          </>
        ) : (
          "Fetch symbol data"
        )}
      </button>
    </div>
  );
}
