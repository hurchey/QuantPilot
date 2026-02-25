// apps/web/src/app/page.tsx
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <h1 className="text-3xl font-bold mb-2">QuantPilot</h1>
        <p className="text-slate-300">
          A quant-focused full-stack SaaS app for uploading market data, defining trading strategies,
          running backtests, and reviewing risk/performance metrics.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link href="/auth/register" className="rounded-xl border border-slate-800 bg-slate-900 p-4 hover:border-slate-700">
          <div className="font-semibold">1) Create Account</div>
          <div className="text-sm text-slate-400 mt-1">Register and create your workspace</div>
        </Link>
        <Link href="/data" className="rounded-xl border border-slate-800 bg-slate-900 p-4 hover:border-slate-700">
          <div className="font-semibold">2) Upload Data</div>
          <div className="text-sm text-slate-400 mt-1">Import OHLCV CSV files</div>
        </Link>
        <Link href="/strategies" className="rounded-xl border border-slate-800 bg-slate-900 p-4 hover:border-slate-700">
          <div className="font-semibold">3) Build Strategy</div>
          <div className="text-sm text-slate-400 mt-1">Define SMA crossover params</div>
        </Link>
        <Link href="/backtests" className="rounded-xl border border-slate-800 bg-slate-900 p-4 hover:border-slate-700">
          <div className="font-semibold">4) Run Backtest</div>
          <div className="text-sm text-slate-400 mt-1">Analyze metrics, trades, and equity</div>
        </Link>
      </section>
    </div>
  );
}