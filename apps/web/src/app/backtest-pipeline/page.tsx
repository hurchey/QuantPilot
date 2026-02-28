"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

import { apiFetch } from "@/lib/api";

export default function BacktestPipelinePage() {
  const [symbol, setSymbol] = useState("AAPL");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [volatility, setVolatility] = useState<Record<string, unknown> | null>(null);
  const [regime, setRegime] = useState<Record<string, unknown> | null>(null);
  const [sentiment, setSentiment] = useState<Record<string, unknown> | null>(null);
  const [sizing, setSizing] = useState<Record<string, unknown> | null>(null);

  const [sizingForm, setSizingForm] = useState({
    method: "vol_target",
    target_vol: "0.15",
    asset_vol: "0.2",
    win_prob: "0.5",
    win_loss_ratio: "1.0",
  });

  async function handleFetchInsights(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setVolatility(null);
    setRegime(null);
    setSentiment(null);

    try {
      const [volRes, regimeRes, sentimentRes] = await Promise.allSettled([
        apiFetch<unknown>(`/quant/backtest-pipeline/volatility/${symbol}`),
        apiFetch<unknown>(`/quant/backtest-pipeline/regime/${symbol}`),
        apiFetch<unknown>(`/quant/backtest-pipeline/sentiment/${symbol}`),
      ]);

      if (volRes.status === "fulfilled") setVolatility(volRes.value as Record<string, unknown>);
      if (regimeRes.status === "fulfilled") setRegime(regimeRes.value as Record<string, unknown>);
      if (sentimentRes.status === "fulfilled") setSentiment(sentimentRes.value as Record<string, unknown>);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch insights.");
    } finally {
      setLoading(false);
    }
  }

  async function handlePositionSizing(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSizing(null);

    try {
      const res = await apiFetch<unknown>(
        `/quant/backtest-pipeline/position-sizing?method=${sizingForm.method}&target_vol=${sizingForm.target_vol}&asset_vol=${sizingForm.asset_vol}&win_prob=${sizingForm.win_prob}&win_loss_ratio=${sizingForm.win_loss_ratio}`
      );
      setSizing(res as Record<string, unknown>);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to compute position size.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {error ? <ErrorBanner title="Error" message={error} error={error} /> : null}

      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Backtest Pipeline</h1>
        <p className="text-sm text-slate-400">
          Volatility, regime detection, sentiment (placeholder), and position sizing.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Stock Insights</h2>
        <p className="mb-3 text-xs text-slate-400">
          Requires market data in DB.{" "}
          <Link href="/data" className="text-blue-400 hover:underline">
            Upload or fetch data
          </Link>{" "}
          first.
        </p>
        <form onSubmit={handleFetchInsights} className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs text-slate-400">Symbol</label>
            <input
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="AAPL"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60"
          >
            {loading ? "Loading..." : "Fetch Insights"}
          </button>
        </form>

        {(volatility || regime || sentiment) && (
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            {volatility && (
              <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-3">
                <h3 className="text-xs font-medium text-slate-400 uppercase">Volatility</h3>
                <p className="mt-1 text-sm text-slate-200">
                  {(volatility.annualized_vol as number)?.toFixed(2) ?? "—"} ann. vol
                </p>
                <p className="text-xs text-slate-400">
                  Label: {(volatility.volatility_label as string) ?? "—"} ({(volatility.vs_average as number)?.toFixed(2) ?? "—"}× avg)
                </p>
              </div>
            )}
            {regime && (
              <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-3">
                <h3 className="text-xs font-medium text-slate-400 uppercase">Regime</h3>
                <p className="mt-1 text-sm text-slate-200 capitalize">{(regime.regime as string) ?? "—"}</p>
                <p className="text-xs text-slate-400">
                  Confidence: {((regime.confidence as number) * 100)?.toFixed(0) ?? "—"}%
                </p>
              </div>
            )}
            {sentiment && (
              <div className="rounded-lg border border-slate-700 bg-slate-950/50 p-3">
                <h3 className="text-xs font-medium text-slate-400 uppercase">Sentiment / Buzz</h3>
                <p className="mt-1 text-lg font-semibold text-slate-200">
                  {(sentiment.composite_score as number)?.toFixed(1) ?? "—"}/100
                </p>
                <p className="text-xs text-slate-400">
                  News: {(sentiment.news_count as number) ?? 0} · Social: {(sentiment.social_count as number) ?? 0}
                </p>
                <p className="text-xs text-slate-400">
                  NLP: {(sentiment.ensemble_sentiment as number)?.toFixed(2) ?? "—"} (conf: {((sentiment.ensemble_confidence as number) * 100)?.toFixed(0) ?? "—"}%)
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Sources: {(sentiment.sources as string[])?.join(", ") ?? "—"}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Position Sizing</h2>
        <form onSubmit={handlePositionSizing} className="grid grid-cols-1 gap-3 md:grid-cols-5">
          <div>
            <label className="mb-1 block text-xs text-slate-400">Method</label>
            <select
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={sizingForm.method}
              onChange={(e) => setSizingForm((p) => ({ ...p, method: e.target.value }))}
            >
              <option value="vol_target">Vol targeting</option>
              <option value="kelly">Kelly</option>
              <option value="fixed">Fixed</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">Target vol</label>
            <input
              type="number"
              step="0.01"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={sizingForm.target_vol}
              onChange={(e) => setSizingForm((p) => ({ ...p, target_vol: e.target.value }))}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">Asset vol</label>
            <input
              type="number"
              step="0.01"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={sizingForm.asset_vol}
              onChange={(e) => setSizingForm((p) => ({ ...p, asset_vol: e.target.value }))}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">Win prob (Kelly)</label>
            <input
              type="number"
              step="0.01"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
              value={sizingForm.win_prob}
              onChange={(e) => setSizingForm((p) => ({ ...p, win_prob: e.target.value }))}
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-60"
            >
              Compute
            </button>
          </div>
        </form>
        {sizing && (
          <div className="mt-4 rounded-lg border border-slate-700 bg-slate-950/50 p-3">
            <p className="text-sm text-slate-200">
              Weight: <span className="font-mono">{(sizing.weight as number)?.toFixed(2) ?? "—"}</span> ({sizing.method as string})
            </p>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-2 text-sm font-medium text-slate-200">Quant Features</h2>
        <ul className="list-inside list-disc space-y-1 text-sm text-slate-400">
          <li>Vol targeting & Kelly position sizing</li>
          <li>Regime detection (trending / mean-reverting / vol)</li>
          <li>Sentiment placeholder (future: Google Trends, news API)</li>
          <li>Risk models: covariance shrinkage, factor exposure</li>
          <li>Online updates: EWMA, RLS, Kalman</li>
        </ul>
        <p className="mt-2 text-xs text-slate-500">
          <Link href="/backtests" className="text-blue-400 hover:underline">
            Back to Backtests
          </Link>
        </p>
      </div>
    </div>
  );
}
