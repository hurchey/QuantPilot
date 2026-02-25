"use client";

import { useEffect, useState } from "react";

import CsvUploadForm from "@/components/data/CsvUploadForm";
import DemoDataForm from "@/components/data/DemoDataForm";
import ParquetUploadForm from "@/components/data/ParquetUploadForm";
import SymbolFetchForm from "@/components/data/SymbolFetchForm";
import EmptyState from "@/components/ui/EmptyState";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import MetricCard from "@/components/ui/MetricCard";

import { apiFetch } from "@/lib/api";

type DatasetRow = {
  id: number | string;
  name?: string;
  symbol?: string;
  timeframe?: string;
  row_count?: number;
  created_at?: string;
};

type DataSourceTab = "demo" | "csv" | "parquet" | "symbol";

const TABS: { id: DataSourceTab; label: string; description: string }[] = [
  { id: "demo", label: "Demo dataset", description: "Easy onboarding" },
  { id: "csv", label: "CSV upload", description: "Custom user files" },
  { id: "parquet", label: "Parquet upload", description: "Quant/data engineering" },
  { id: "symbol", label: "Symbol fetch", description: "Real product workflow" },
];

function toArray<T = unknown>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export default function DataPage() {
  const [datasets, setDatasets] = useState<DatasetRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DataSourceTab>("demo");

  const CsvUploadFormAny = CsvUploadForm as React.ComponentType<any>;
  const ErrorBannerAny = ErrorBanner as React.ComponentType<any>;
  const LoadingSpinnerAny = LoadingSpinner as React.ComponentType<any>;
  const EmptyStateAny = EmptyState as React.ComponentType<any>;
  const MetricCardAny = MetricCard as React.ComponentType<any>;

  async function loadDatasets(showSpinner = true) {
    if (showSpinner) setLoading(true);
    else setRefreshing(true);
    setError(null);

    try {
      let res: unknown;
      try {
        res = await apiFetch("/quant/data");
      } catch {
        res = await apiFetch("/quant/datasets");
      }

      const rows = toArray<Record<string, unknown>>(res);
      const normalized = rows.map((d, idx) => ({
        id: (d.id as number | string) ?? idx,
        name: String(d.name ?? d.file_name ?? d.filename ?? `Dataset ${idx + 1}`),
        symbol: d.symbol ? String(d.symbol) : "",
        timeframe: d.timeframe ? String(d.timeframe) : "",
        row_count: Number(d.row_count ?? d.rows ?? d.num_rows ?? 0),
        created_at: d.created_at ? String(d.created_at) : "",
      }));
      setDatasets(normalized);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load datasets.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadDatasets(true);
  }, []);

  const onDataSuccess = async () => {
    await loadDatasets(false);
  };

  const totalRows = datasets.reduce((sum, d) => sum + (d.row_count || 0), 0);

  return (
    <div className="space-y-6">
      {error ? (
        <ErrorBannerAny title="Market Data Error" message={error} error={error} />
      ) : null}

      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Market Data</h1>
          <p className="text-sm text-slate-400">
            Add OHLCV data for backtesting: demo, CSV, Parquet, or fetch from API.
          </p>
        </div>
        <button
          onClick={() => loadDatasets(false)}
          className="inline-flex items-center rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm hover:bg-slate-800"
        >
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCardAny title="Datasets" value={String(datasets.length)} subtitle="Loaded" />
        <MetricCardAny title="Total Rows" value={String(totalRows)} subtitle="Price bars" />
        <MetricCardAny
          title="Symbols"
          value={String(new Set(datasets.map((d) => d.symbol).filter(Boolean)).size)}
          subtitle="Unique tickers"
        />
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <div className="mb-4 flex flex-wrap gap-2 border-b border-slate-800 pb-3">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? "bg-slate-700 text-slate-100"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <h2 className="mb-3 text-sm font-medium text-slate-200">
          {TABS.find((t) => t.id === activeTab)?.description}
        </h2>

        {activeTab === "demo" && (
          <DemoDataForm onSuccess={onDataSuccess} />
        )}
        {activeTab === "csv" && (
          <CsvUploadFormAny
            onUploaded={onDataSuccess}
            onUploadedAction={onDataSuccess}
            onSuccess={onDataSuccess}
            onSuccessAction={onDataSuccess}
          />
        )}
        {activeTab === "parquet" && (
          <ParquetUploadForm onSuccess={onDataSuccess} />
        )}
        {activeTab === "symbol" && (
          <SymbolFetchForm onSuccess={onDataSuccess} />
        )}
      </div>

      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-200">Available Datasets</h2>
        {loading ? (
          <LoadingSpinnerAny label="Loading datasets..." />
        ) : datasets.length === 0 ? (
          <EmptyStateAny
            title="No market data yet"
            description="Load demo data, upload a file, or fetch a symbol to get started."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-slate-400">
                <tr className="border-b border-slate-800">
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Symbol</th>
                  <th className="px-3 py-2">Timeframe</th>
                  <th className="px-3 py-2">Rows</th>
                  <th className="px-3 py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={String(d.id)} className="border-b border-slate-800/60">
                    <td className="px-3 py-2 font-medium text-slate-100">{d.name || "—"}</td>
                    <td className="px-3 py-2 text-slate-300">{d.symbol || "—"}</td>
                    <td className="px-3 py-2 text-slate-300">{d.timeframe || "—"}</td>
                    <td className="px-3 py-2 text-slate-300">{d.row_count ?? 0}</td>
                    <td className="px-3 py-2 text-slate-400">
                      {d.created_at ? new Date(d.created_at).toLocaleString() : "—"}
                    </td>
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
