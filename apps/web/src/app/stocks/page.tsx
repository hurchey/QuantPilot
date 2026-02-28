"use client";

import { useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import MetricCard from "@/components/ui/MetricCard";
import { apiFetch, apiPost } from "@/lib/api";

type StockInfo = Record<string, unknown>;
type GreeksResponse = {
  symbol?: string;
  expiry?: string;
  underlyingPrice?: number;
  atmStrike?: number;
  impliedVolatility?: number;
  call?: { delta?: number; gamma?: number; theta?: number; vega?: number };
  put?: { delta?: number; gamma?: number; theta?: number; vega?: number };
};
type Greeks = { delta?: number; gamma?: number; theta?: number; vega?: number; rho?: number };

type OptionRow = {
  strike?: number;
  bid?: number;
  ask?: number;
  last?: number;
  volume?: number;
  openInterest?: number;
  impliedVolatility?: number;
  greeks?: Greeks;
};

type OptionChainData = {
  symbol?: string;
  expirations?: string[];
  expiry?: string;
  calls?: OptionRow[];
  puts?: OptionRow[];
  underlying_price?: number;
};

type DividendRow = { date?: string; amount?: number; currency?: string };

type RatesData = { rate?: number; as_of?: string };
type SnapshotRow = { symbol?: string; snapshot_at?: string; expiry?: string };

function SetRateForm({ onSubmit }: { onSubmit: (date: string, rate: number) => void }) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [ratePct, setRatePct] = useState("5");
  const [submitting, setSubmitting] = useState(false);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        const rate = ratePct ? Number(ratePct) / 100 : 0.05;
        if (!Number.isFinite(rate) || rate < 0 || rate > 0.5) return;
        setSubmitting(true);
        onSubmit(date, rate);
        setSubmitting(false);
      }}
      className="flex flex-wrap items-end gap-3"
    >
      <div>
        <label className="mb-1 block text-xs text-slate-500">Date</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="rounded-lg border border-slate-600 bg-slate-800 px-2 py-1.5 text-xs"
        />
      </div>
      <div>
        <label className="mb-1 block text-xs text-slate-500">Rate (%)</label>
        <input
          type="number"
          min={0}
          max={50}
          step={0.1}
          value={ratePct}
          onChange={(e) => setRatePct(e.target.value)}
          placeholder="5"
          className="w-20 rounded-lg border border-slate-600 bg-slate-800 px-2 py-1.5 text-xs"
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800 disabled:opacity-50"
      >
        {submitting ? "Saving..." : "Save"}
      </button>
    </form>
  );
}

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
  const [greeks, setGreeks] = useState<GreeksResponse | null>(null);
  const [optionChain, setOptionChain] = useState<OptionChainData | null>(null);
  const [rates, setRates] = useState<RatesData | null>(null);
  const [dividends, setDividends] = useState<DividendRow[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [greeksLoading, setGreeksLoading] = useState(false);
  const [chainLoading, setChainLoading] = useState(false);
  const [ratesLoading, setRatesLoading] = useState(false);
  const [dividendsLoading, setDividendsLoading] = useState(false);
  const [snapshotLoading, setSnapshotLoading] = useState(false);
  const [snapshots, setSnapshots] = useState<SnapshotRow[] | null>(null);
  const [snapshotsLoading, setSnapshotsLoading] = useState(false);
  const [ratesHistory, setRatesHistory] = useState<{ date?: string; rate?: number; source?: string }[] | null>(null);
  const [ratesHistoryLoading, setRatesHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLookup() {
    setError(null);
    setInfo(null);
    setGreeks(null);
    setOptionChain(null);
    setDividends(null);
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

  async function handleLoadOptionChain(expiry?: string, withGreeks = true) {
    setError(null);
    setChainLoading(true);
    try {
      const params = new URLSearchParams();
      if (expiry) params.set("expiry", expiry);
      if (withGreeks) params.set("include_greeks", "true");
      const url = `/quant/options/${symbol.toUpperCase()}/chain?${params}`;
      const data = await apiFetch<OptionChainData>(url);
      setOptionChain(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch option chain");
    } finally {
      setChainLoading(false);
    }
  }

  async function handleLoadRates() {
    setError(null);
    setRatesLoading(true);
    try {
      const data = await apiFetch<RatesData>("/quant/options/rates");
      setRates(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch rates");
    } finally {
      setRatesLoading(false);
    }
  }

  async function handleLoadDividends() {
    setError(null);
    setDividendsLoading(true);
    try {
      const data = await apiFetch<DividendRow[]>("/quant/options/dividends/" + symbol.toUpperCase());
      setDividends(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch dividends");
    } finally {
      setDividendsLoading(false);
    }
  }

  async function handleSaveSnapshot() {
    setError(null);
    setSnapshotLoading(true);
    try {
      const expiry = optionChain?.expiry;
      const url = expiry
        ? `/quant/options/${symbol.toUpperCase()}/snapshot?expiry=${expiry}`
        : `/quant/options/${symbol.toUpperCase()}/snapshot`;
      await apiPost(url);
      setSnapshots(null); // invalidate so user can refresh
      handleLoadSnapshots();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save snapshot. Log in to save.");
    } finally {
      setSnapshotLoading(false);
    }
  }

  async function handleLoadSnapshots() {
    setError(null);
    setSnapshotsLoading(true);
    try {
      const data = await apiFetch<SnapshotRow[]>(
        `/quant/options/${symbol.toUpperCase()}/snapshots?limit=20`
      );
      setSnapshots(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load snapshots. Log in to view.");
      setSnapshots([]);
    } finally {
      setSnapshotsLoading(false);
    }
  }

  async function handleLoadRatesHistory() {
    setError(null);
    setRatesHistoryLoading(true);
    try {
      const data = await apiFetch<{ date?: string; rate?: number; source?: string }[]>(
        "/quant/options/rates/history?limit=20"
      );
      setRatesHistory(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load rates history");
    } finally {
      setRatesHistoryLoading(false);
    }
  }

  async function handleSetRate(date: string, rate: number) {
    setError(null);
    try {
      await apiPost(
        `/quant/options/rates?date=${encodeURIComponent(date)}&rate=${rate}&source=manual`
      );
      handleLoadRates();
      handleLoadRatesHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save rate");
    }
  }

  async function handleSyncDividends() {
    setError(null);
    setDividendsLoading(true);
    try {
      await apiPost(`/quant/options/dividends/${symbol.toUpperCase()}/sync`);
      handleLoadDividends();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to sync dividends");
    } finally {
      setDividendsLoading(false);
    }
  }

  async function handleLoadGreeks() {
    setError(null);
    setGreeksLoading(true);

    try {
      const data = await apiFetch<GreeksResponse>(`/quant/stocks/${symbol.toUpperCase()}/greeks`);
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
          <LoadingSpinner text="Fetching stock data..." />
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

          {/* Option Chain */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-sm font-medium text-slate-200">Option Chain</h2>
              <div className="flex flex-wrap items-center gap-2">
                {optionChain?.expirations && optionChain.expirations.length > 0 && (
                  <select
                    value={optionChain.expiry ?? ""}
                    onChange={(e) => handleLoadOptionChain(e.target.value || undefined)}
                    className="rounded-lg border border-slate-600 bg-slate-800 px-2 py-1.5 text-xs text-slate-200"
                  >
                    {optionChain.expirations.slice(0, 12).map((exp) => (
                      <option key={exp} value={exp}>{exp}</option>
                    ))}
                  </select>
                )}
                <button
                  onClick={() => handleLoadOptionChain()}
                  disabled={chainLoading}
                  className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800 disabled:opacity-50"
                >
                  {chainLoading ? "Loading..." : optionChain ? "Refresh" : "Load Chain"}
                </button>
                {optionChain && (
                  <button
                    onClick={handleSaveSnapshot}
                    disabled={snapshotLoading}
                    className="rounded-lg border border-emerald-600/60 bg-emerald-600/20 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-600/30 disabled:opacity-50"
                    title="Save this chain to your workspace for backtesting"
                  >
                    {snapshotLoading ? "Saving..." : "Save to workspace"}
                  </button>
                )}
              </div>
            </div>
            {optionChain ? (
              <div className="space-y-4">
                {optionChain.underlying_price != null && (
                  <p className="text-xs text-slate-500">
                    Underlying: ${formatNum(optionChain.underlying_price)} · Expiry: {optionChain.expiry}
                    {(optionChain.calls ?? [])[0]?.greeks && (
                      <span className="ml-2">· Δ delta, Γ gamma, Θ theta (/day), V vega</span>
                    )}
                  </p>
                )}
                <div className="overflow-x-auto">
                  <div className="max-h-96 overflow-y-auto rounded-lg border border-slate-700">
                    <table className="w-full text-xs">
                      <thead className="sticky top-0 bg-slate-900">
                        <tr className="text-left text-slate-500">
                          <th colSpan={4} className="p-2 text-center border-r border-slate-700 bg-slate-800/60">Calls</th>
                          <th className="p-2 bg-slate-900 font-medium">Strike</th>
                          <th colSpan={4} className="p-2 text-center border-l border-slate-700 bg-slate-800/60">Puts</th>
                          {(optionChain.calls ?? [])[0]?.greeks && (
                            <>
                              <th colSpan={4} className="p-2 text-center border-l border-slate-700 bg-slate-800/60">Call Greeks</th>
                              <th colSpan={4} className="p-2 text-center border-l border-slate-700 bg-slate-800/60">Put Greeks</th>
                            </>
                          )}
                        </tr>
                        <tr className="text-left text-slate-500">
                          <th className="p-2">Bid</th>
                          <th className="p-2">Ask</th>
                          <th className="p-2">IV</th>
                          <th className="p-2 border-r border-slate-700">Last</th>
                          <th className="p-2 font-medium"></th>
                          <th className="p-2 border-l border-slate-700">Bid</th>
                          <th className="p-2">Ask</th>
                          <th className="p-2">IV</th>
                          <th className="p-2">Last</th>
                          {(optionChain.calls ?? [])[0]?.greeks && (
                            <>
                              <th className="p-2 border-l border-slate-700">Δ</th>
                              <th className="p-2">Γ</th>
                              <th className="p-2">Θ</th>
                              <th className="p-2">V</th>
                              <th className="p-2 border-l border-slate-700">Δ</th>
                              <th className="p-2">Γ</th>
                              <th className="p-2">Θ</th>
                              <th className="p-2">V</th>
                            </>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {(() => {
                          const calls = optionChain?.calls ?? [];
                          const puts = optionChain?.puts ?? [];
                          const strikes = [...new Set([...calls.map((c) => c.strike), ...puts.map((p) => p.strike)])].filter((s): s is number => s != null).sort((a, b) => a - b);
                          const callMap = new Map(calls.map((c) => [c.strike, c]));
                          const putMap = new Map(puts.map((p) => [p.strike, p]));
                          return strikes.map((strike) => {
                            const c = callMap.get(strike);
                            const p = putMap.get(strike);
                            return (
                              <tr key={strike} className="border-t border-slate-800">
                                <td className="p-2">{formatNum(c?.bid)}</td>
                                <td className="p-2">{formatNum(c?.ask)}</td>
                                <td className="p-2">{c?.impliedVolatility != null ? formatPct(c.impliedVolatility * 100) : "—"}</td>
                                <td className="p-2 border-r border-slate-700">{formatNum(c?.last)}</td>
                                <td className="p-2 font-medium">{formatNum(strike)}</td>
                                <td className="p-2 border-l border-slate-700">{formatNum(p?.bid)}</td>
                                <td className="p-2">{formatNum(p?.ask)}</td>
                                <td className="p-2">{p?.impliedVolatility != null ? formatPct(p.impliedVolatility * 100) : "—"}</td>
                                <td className="p-2">{formatNum(p?.last)}</td>
                                {c?.greeks && (
                                  <>
                                    <td className="p-2 border-l border-slate-700 text-slate-400">{formatNum(c.greeks.delta)}</td>
                                    <td className="p-2 text-slate-400">{formatNum(c.greeks.gamma)}</td>
                                    <td className="p-2 text-slate-400">{formatNum(c.greeks.theta)}</td>
                                    <td className="p-2 text-slate-400">{formatNum(c.greeks.vega)}</td>
                                    <td className="p-2 border-l border-slate-700 text-slate-400">{formatNum(p?.greeks?.delta)}</td>
                                    <td className="p-2 text-slate-400">{formatNum(p?.greeks?.gamma)}</td>
                                    <td className="p-2 text-slate-400">{formatNum(p?.greeks?.theta)}</td>
                                    <td className="p-2 text-slate-400">{formatNum(p?.greeks?.vega)}</td>
                                  </>
                                )}
                              </tr>
                            );
                          });
                        })()}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                Full option chain with strikes, bid/ask, and implied volatility. Click &quot;Load Chain&quot; to fetch.
              </p>
            )}
            {/* Saved snapshots */}
            <div className="mt-4 border-t border-slate-800 pt-4">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-xs font-medium text-slate-400">Your saved snapshots</h3>
                <button
                  onClick={handleLoadSnapshots}
                  disabled={snapshotsLoading}
                  className="text-xs text-slate-500 hover:text-slate-400 disabled:opacity-50"
                >
                  {snapshotsLoading ? "Loading..." : "Refresh list"}
                </button>
              </div>
              {snapshots && snapshots.length > 0 ? (
                <div className="max-h-24 overflow-y-auto rounded border border-slate-700 text-xs">
                  <table className="w-full">
                    <thead className="bg-slate-800/60">
                      <tr className="text-left text-slate-500">
                        <th className="p-2">Symbol</th>
                        <th className="p-2">Snapshot at</th>
                        <th className="p-2">Expiry</th>
                      </tr>
                    </thead>
                    <tbody>
                      {snapshots.map((s, i) => (
                        <tr key={i} className="border-t border-slate-800">
                          <td className="p-2">{s.symbol}</td>
                          <td className="p-2 text-slate-400">{s.snapshot_at ?? "—"}</td>
                          <td className="p-2">{s.expiry ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : snapshots ? (
                <p className="text-xs text-slate-500">No saved snapshots. Load a chain and click &quot;Save to workspace&quot; (requires login).</p>
              ) : (
                <p className="text-xs text-slate-500">Click &quot;Refresh list&quot; to see saved snapshots (requires login).</p>
              )}
            </div>
          </div>

          {/* Risk-Free Rates */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-sm font-medium text-slate-200">Risk-Free Rate</h2>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleLoadRates}
                  disabled={ratesLoading}
                  className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800 disabled:opacity-50"
                >
                  {ratesLoading ? "Loading..." : rates ? "Refresh" : "Load Rate"}
                </button>
                <button
                  onClick={handleLoadRatesHistory}
                  disabled={ratesHistoryLoading}
                  className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800 disabled:opacity-50"
                >
                  {ratesHistoryLoading ? "Loading..." : "History"}
                </button>
              </div>
            </div>
            {rates ? (
              <p className="text-sm text-slate-300">
                Current rate: <strong>{formatPct((rates.rate ?? 0) * 100)}</strong>
                {rates.as_of && <span className="ml-2 text-slate-500">(as of {rates.as_of})</span>}
              </p>
            ) : (
              <p className="text-sm text-slate-500">
                Risk-free rate used for options pricing and Greeks. Click &quot;Load Rate&quot; to fetch.
              </p>
            )}
            {/* Set rate form */}
            <div className="mt-4 border-t border-slate-800 pt-4">
              <h3 className="mb-2 text-xs font-medium text-slate-400">Set rate for a date</h3>
              <SetRateForm onSubmit={handleSetRate} />
            </div>
            {/* Rates history */}
            {ratesHistory && ratesHistory.length > 0 && (
              <div className="mt-4 border-t border-slate-800 pt-4">
                <h3 className="mb-2 text-xs font-medium text-slate-400">Stored rates</h3>
                <div className="max-h-32 overflow-y-auto rounded border border-slate-700 text-xs">
                  <table className="w-full">
                    <thead className="sticky top-0 bg-slate-900">
                      <tr className="text-left text-slate-500">
                        <th className="p-2">Date</th>
                        <th className="p-2">Rate</th>
                        <th className="p-2">Source</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ratesHistory.map((r, i) => (
                        <tr key={i} className="border-t border-slate-800">
                          <td className="p-2">{r.date ?? "—"}</td>
                          <td className="p-2">{r.rate != null ? formatPct(r.rate * 100) : "—"}</td>
                          <td className="p-2 text-slate-500">{r.source ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Dividends */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-sm font-medium text-slate-200">Dividends</h2>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleLoadDividends}
                  disabled={dividendsLoading}
                  className="rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800 disabled:opacity-50"
                >
                  {dividendsLoading ? "Loading..." : dividends ? "Refresh" : "Load Dividends"}
                </button>
                <button
                  onClick={handleSyncDividends}
                  disabled={dividendsLoading}
                  className="rounded-lg border border-emerald-600/60 bg-emerald-600/20 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-600/30 disabled:opacity-50"
                  title="Persist dividends to database for backtesting"
                >
                  Sync to database
                </button>
              </div>
            </div>
            {dividends && dividends.length > 0 ? (
              <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-700">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-slate-900">
                    <tr className="text-left text-slate-500">
                      <th className="p-2">Ex-Date</th>
                      <th className="p-2">Amount</th>
                      <th className="p-2">Currency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dividends.map((d, i) => (
                      <tr key={i} className="border-t border-slate-800">
                        <td className="p-2">{d.date ?? "—"}</td>
                        <td className="p-2">${formatNum(d.amount)}</td>
                        <td className="p-2">{d.currency ?? "USD"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : dividends && dividends.length === 0 ? (
              <p className="text-sm text-slate-500">No dividend history for this symbol.</p>
            ) : (
              <p className="text-sm text-slate-500">
                Dividend history for options pricing and corporate actions. Click &quot;Load Dividends&quot; to fetch.
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
