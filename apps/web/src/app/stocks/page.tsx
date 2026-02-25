"use client";

import { useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import MetricCard from "@/components/ui/MetricCard";
import { apiFetch } from "@/lib/api";

type StockInfo = Record<string, unknown>;
type Greeks = {
  symbol?: string;
  expiry?: string;
  underlyingPrice?: number;
  atmStrike?: number;
  impliedVolatility?: number;
  call?: { delta?: number; gamma?: number; theta?: number; vega?: number };
  put?: { delta?: number; gamma?: number; theta?: number; vega?: number };
};

function formatNum(v: unknown): string {
  if (v == null) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 1e9) return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
  if (Math.abs(n) >= 1) return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return n.toFixed(4);
}

function formatPct(v: unknown): string {
  if (v == null) return "—";
  const n = Number(v);
  if (!Number.isFinite(n)) return "—";
  return `${n.toFixed(2)}%`;
}

export default function StocksPage() {
  const [symbol, setSymbol] = useState("SPY");
  const [info, setInfo] = useState<StockInfo | null>(null);
  const [greeks, setGreeks] = useState<Greeks | null>(null);
  const [loading, setLoading] = useState(false);
  const [greeksLoading, setGreeksLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLookup() {
    setError(null);
    setInfo(null);
    setGreeks(null);
    setLoading(true);

    try {
      const data = await apiFetch<StockInfo>(`/quant/stocks/${symbol.toUpperCase()}/info`);
      setInfo(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch stock info");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadGreeks() {
    setError(null);
    setGreeksLoading(true);

    try {
      const data = await apiFetch<Greeks>(`/quant/stocks/${symbol.toUpperCase()}/greeks`);
      setGreeks(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch Greeks");
    } finally {
      setGreeksLoading(false);
    }
  }

  const changePercent = info?.changePercent != null ? Number(info.changePercent) : null;
  const isPositive = changePercent != null && changePercent > 0;
  const isNegative = changePercent != null && changePercent < 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Stock Profile</h1>
        <p className="text-sm text-slate-400">
          Deep-dive into a single stock: pricing, 52-week range, all-time highs/lows, and options Greeks.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-slate-400">Symbol</label>
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && handleLookup()}
              placeholder="SPY"
              className="w-32 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={handleLookup}
            disabled={loading}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {loading ? "Loading..." : "Look up"}
          </button>
        </div>
      </div>

      {error && (
        <ErrorBanner title="Error" message={error} onDismissAction={() => setError(null)} />
      )}

      {loading && (
        <div className="py-12">
          <LoadingSpinner label="Fetching stock data..." />
        </div>
      )}

      {info && !loading && (
        <>
          {/* Header: name, price, change */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <div className="flex flex-wrap items-baseline gap-4">
              <h2 className="text-xl font-semibold">
                {String(info.shortName ?? info.longName ?? info.symbol ?? symbol)}
              </h2>
              <span className="text-slate-400">{String(info.symbol ?? symbol)}</span>
              <span className="text-2xl font-bold text-slate-100">
                ${formatNum(info.currentPrice ?? info.regularMarketPrice)}
              </span>
              {changePercent != null && (
                <span
                  className={`text-sm font-medium ${
                    isPositive ? "text-emerald-400" : isNegative ? "text-red-400" : "text-slate-400"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {formatPct(changePercent)} ({info.changeFromPrevious != null ? `$${formatNum(info.changeFromPrevious)}` : ""})
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-slate-500">
              Data from Yahoo Finance · {info.fetchedAt ? new Date(String(info.fetchedAt)).toLocaleString() : ""}
            </p>
          </div>

          {/* Pricing metrics */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard
              title="Previous close"
              value={`$${formatNum(info.previousClose)}`}
              subvalue="Prior session"
            />
            <MetricCard
              title="Day high / low"
              value={`$${formatNum(info.dayHigh)} / $${formatNum(info.dayLow)}`}
              subvalue="Today"
            />
            <MetricCard
              title="52-week high / low"
              value={`$${formatNum(info.fiftyTwoWeekHigh)} / $${formatNum(info.fiftyTwoWeekLow)}`}
              subvalue="Year range"
            />
            <MetricCard
              title="All-time high / low"
              value={`$${formatNum(info.allTimeHigh)} / $${formatNum(info.allTimeLow)}`}
              subvalue="Historical"
            />
          </div>

          {/* Volume & fundamentals */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <MetricCard title="Volume" value={formatNum(info.volume)} subvalue="Today" />
            <MetricCard title="Avg volume" value={formatNum(info.averageVolume)} subvalue="10-day" />
            <MetricCard title="Market cap" value={`$${formatNum(info.marketCap)}`} subvalue="" />
            <MetricCard title="Beta" value={formatNum(info.beta)} subvalue="vs market" />
            <MetricCard title="P/E (TTM)" value={formatNum(info.trailingPE)} subvalue="Trailing" />
            <MetricCard title="Div yield" value={formatPct(info.dividendYield)} subvalue="Annual" />
          </div>

          {/* Greeks */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium text-slate-200">Options Greeks (ATM)</h2>
              <button
                onClick={handleLoadGreeks}
                disabled={greeksLoading}
                className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800 disabled:opacity-50"
              >
                {greeksLoading ? "Loading..." : "Load Greeks"}
              </button>
            </div>
            {greeks ? (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-4">
                  <h3 className="mb-2 text-xs font-medium text-slate-400">Call (ATM)</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-slate-500">Delta</span> {formatNum(greeks.call?.delta)}</div>
                    <div><span className="text-slate-500">Gamma</span> {formatNum(greeks.call?.gamma)}</div>
                    <div><span className="text-slate-500">Theta</span> {formatNum(greeks.call?.theta)}</div>
                    <div><span className="text-slate-500">Vega</span> {formatNum(greeks.call?.vega)}</div>
                  </div>
                </div>
                <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-4">
                  <h3 className="mb-2 text-xs font-medium text-slate-400">Put (ATM)</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-slate-500">Delta</span> {formatNum(greeks.put?.delta)}</div>
                    <div><span className="text-slate-500">Gamma</span> {formatNum(greeks.put?.gamma)}</div>
                    <div><span className="text-slate-500">Theta</span> {formatNum(greeks.put?.theta)}</div>
                    <div><span className="text-slate-500">Vega</span> {formatNum(greeks.put?.vega)}</div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                Greeks are computed from ATM options using Black-Scholes. Click &quot;Load Greeks&quot; to fetch.
              </p>
            )}
          </div>
        </>
      )}

      {!info && !loading && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <p className="text-slate-400">Enter a symbol (e.g. SPY, AAPL, MSFT) and click Look up.</p>
        </div>
      )}
    </div>
  );
}
