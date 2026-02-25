"use client";

import React, { useState } from "react";
import Link from "next/link";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { apiFetch } from "@/lib/api";

type QuickAddMarketDataProps = {
  onSuccess?: () => void;
  className?: string;
};

export default function QuickAddMarketData({ onSuccess, className = "" }: QuickAddMarketDataProps) {
  const [activeSource, setActiveSource] = useState<"demo" | "symbol">("demo");
  const [symbol, setSymbol] = useState("SPY");
  const [days, setDays] = useState(365);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  async function handleLoadDemo() {
    setError("");
    setSuccessMessage("");
    setLoading(true);
    try {
      const res = await apiFetch<{ rows_inserted: number; symbol: string }>(
        "/quant/data/load-demo",
        {
          method: "POST",
          body: JSON.stringify({ symbol, timeframe: "1d", num_days: 252 }),
        }
      );
      setSuccessMessage(`Loaded ${res?.rows_inserted ?? 0} bars of ${res?.symbol ?? symbol}.`);
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo");
    } finally {
      setLoading(false);
    }
  }

  async function handleFetchSymbol() {
    setError("");
    setSuccessMessage("");
    setLoading(true);
    try {
      const res = await apiFetch<{ rows_inserted: number; symbol: string }>(
        "/quant/data/fetch-symbol",
        {
          method: "POST",
          body: JSON.stringify({ symbol, timeframe: "1d", days }),
        }
      );
      setSuccessMessage(`Fetched ${res?.rows_inserted ?? 0} bars of ${res?.symbol ?? symbol}.`);
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
        Add market data to run backtests. Demo data is synthetic; Symbol fetch uses real Yahoo Finance data.
      </p>

      {error ? (
        <ErrorBanner title="Error" message={error} onDismissAction={() => setError("")} />
      ) : null}
      {successMessage ? (
        <div className="rounded-lg border border-emerald-800/70 bg-emerald-950/20 px-3 py-2 text-sm text-emerald-200">
          {successMessage}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setActiveSource("demo")}
          className={`rounded-lg px-3 py-1.5 text-sm ${
            activeSource === "demo"
              ? "bg-slate-700 text-slate-100"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          Demo
        </button>
        <button
          type="button"
          onClick={() => setActiveSource("symbol")}
          className={`rounded-lg px-3 py-1.5 text-sm ${
            activeSource === "symbol"
              ? "bg-slate-700 text-slate-100"
              : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          }`}
        >
          Symbol fetch
        </button>
      </div>

      {activeSource === "demo" && (
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="SPY"
              className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
            />
          </div>
          <button
            type="button"
            onClick={handleLoadDemo}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
          >
            {loading ? <LoadingSpinner size="sm" /> : null}
            Load demo
          </button>
        </div>
      )}

      {activeSource === "symbol" && (
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="SPY"
              className="w-24 rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Days</label>
            <input
              type="number"
              value={days}
              onChange={(e) => setDays(Math.max(1, Math.min(3650, Number(e.target.value) || 365)))}
              min={1}
              max={3650}
              className="w-20 rounded border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
            />
          </div>
          <button
            type="button"
            onClick={handleFetchSymbol}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-slate-700 px-3 py-1.5 text-sm font-medium text-slate-100 hover:bg-slate-600 disabled:opacity-50"
          >
            {loading ? <LoadingSpinner size="sm" /> : null}
            Fetch
          </button>
        </div>
      )}

      <p className="text-xs text-slate-500">
        For CSV or Parquet uploads,{" "}
        <Link href="/data" className="text-slate-400 hover:text-slate-200 underline">
          go to Market Data
        </Link>
        .
      </p>
    </div>
  );
}
