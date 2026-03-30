"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import MetricCard from "@/components/ui/MetricCard";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import EmptyState from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { formatNumber, formatPercent } from "@/lib/format";

type DatasetStats = {
  total_events: number;
  label_a_count: number;
  label_b_count: number;
  continuation_rate: number | null;
  bucket_distribution: Record<string, number>;
  top_symbols: Array<{ symbol: string; count: number }>;
};

type DislocationEvent = {
  id: number;
  symbol: string;
  company_name: string | null;
  event_start_date: string;
  return_3d_pct: number;
  return_1d_pct: number | null;
  price_start: number;
  price_peak: number;
  label_a: number;
  label_b: number;
  taxonomy_bucket: string | null;
  sector: string | null;
  volume_ratio: number | null;
  short_pct_float: number | null;
  day_after_continuation: number | null;
};

type ScanFormState = {
  symbols: string;
  start_date: string;
  min_return_3d_pct: string;
};

export default function ResearchPage() {
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [events, setEvents] = useState<DislocationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [labelFilter, setLabelFilter] = useState<string>("");
  const [bucketFilter, setBucketFilter] = useState<string>("");

  // Scan form
  const [scanForm, setScanForm] = useState<ScanFormState>({
    symbols: "",
    start_date: "2019-01-01",
    min_return_3d_pct: "500",
  });
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<string | null>(null);

  // Enrich / classify
  const [enriching, setEnriching] = useState(false);
  const [classifying, setClassifying] = useState(false);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (labelFilter) params.set("label", labelFilter);
      if (bucketFilter) params.set("taxonomy_bucket", bucketFilter);
      params.set("limit", "100");

      const [statsRes, eventsRes] = await Promise.all([
        apiGet<DatasetStats>("/quant/research/stats"),
        apiGet<DislocationEvent[]>(`/quant/research/events?${params}`),
      ]);
      setStats(statsRes);
      setEvents(eventsRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load research data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [labelFilter, bucketFilter]);

  async function handleScan() {
    const symbols = scanForm.symbols
      .split(/[,\s]+/)
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);

    if (symbols.length === 0) return;

    setScanning(true);
    setScanResult(null);
    try {
      const res = await apiPost<{
        total_symbols_scanned: number;
        total_events_found: number;
      }>("/quant/research/scan", {
        symbols,
        start_date: scanForm.start_date,
        min_return_3d_pct: Number(scanForm.min_return_3d_pct),
      });
      setScanResult(
        `SCAN COMPLETE // ${res.total_symbols_scanned} scanned // ${res.total_events_found} events detected`
      );
      loadData();
    } catch (err) {
      setScanResult(
        `SCAN ERROR // ${err instanceof Error ? err.message : "Unknown"}`
      );
    } finally {
      setScanning(false);
    }
  }

  async function handleEnrich() {
    setEnriching(true);
    try {
      const res = await apiPost<{ events_enriched: number }>("/quant/research/enrich", {});
      setScanResult(`ENRICHED // ${res.events_enriched} events updated`);
      loadData();
    } catch (err) {
      setScanResult(`ENRICH ERROR // ${err instanceof Error ? err.message : "Unknown"}`);
    } finally {
      setEnriching(false);
    }
  }

  async function handleClassify() {
    setClassifying(true);
    try {
      const res = await apiPost<{
        events_classified: number;
        bucket_counts: Record<string, number>;
      }>("/quant/research/classify", {});
      setScanResult(
        `CLASSIFIED // ${res.events_classified} events // ${Object.keys(res.bucket_counts).length} buckets`
      );
      loadData();
    } catch (err) {
      setScanResult(`CLASSIFY ERROR // ${err instanceof Error ? err.message : "Unknown"}`);
    } finally {
      setClassifying(false);
    }
  }

  async function handleExport(format: "json" | "csv") {
    const params = new URLSearchParams({ format });
    if (labelFilter) params.set("label", labelFilter);
    if (bucketFilter) params.set("taxonomy_bucket", bucketFilter);

    try {
      const url = `/quant/research/export?${params}`;
      if (format === "csv") {
        window.open(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000"}${url}`, "_blank");
      } else {
        const data = await apiGet(url);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = "dislocations.json";
        a.click();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    }
  }

  if (loading && !stats) {
    return (
      <div className="py-16 flex justify-center">
        <LoadingSpinner text="LOADING RESEARCH DATA..." />
      </div>
    );
  }

  const buckets = stats ? Object.keys(stats.bucket_distribution) : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-[0.15em] uppercase text-white">
            Research Hub
          </h1>
          <p className="text-[0.7rem] text-neutral-600 tracking-wide mt-1">
            Extreme dislocation discovery // event scanning // universe building
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/research/universe"
            className="border border-neutral-700 px-3 py-1.5 text-[0.65rem] uppercase tracking-wider text-neutral-400 hover:border-white hover:text-white transition-all"
          >
            Universe Builder
          </Link>
          <Button variant="secondary" size="sm" onClick={() => handleExport("csv")}>
            Export CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport("json")}>
            Export JSON
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismissAction={() => setError(null)} />}

      {/* Stats overview */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricCard
            label="Total Events"
            value={formatNumber(stats.total_events, { maximumFractionDigits: 0 })}
          />
          <MetricCard
            label="Label A (500%+)"
            value={formatNumber(stats.label_a_count, { maximumFractionDigits: 0 })}
          />
          <MetricCard
            label="Label B (1000%+)"
            value={formatNumber(stats.label_b_count, { maximumFractionDigits: 0 })}
          />
          <MetricCard
            label="Continuation Rate"
            value={
              stats.continuation_rate != null
                ? formatPercent(stats.continuation_rate * 100)
                : "--"
            }
          />
          <MetricCard
            label="Taxonomy Buckets"
            value={String(Object.keys(stats.bucket_distribution).length)}
          />
          <MetricCard
            label="Top Symbol"
            value={stats.top_symbols[0]?.symbol ?? "--"}
            subvalue={
              stats.top_symbols[0]
                ? `${stats.top_symbols[0].count} events`
                : undefined
            }
          />
        </div>
      )}

      {/* Scan panel */}
      <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500">
            Symbol Scanner
          </h2>
          {scanning && (
            <span className="text-[0.6rem] text-neutral-600 uppercase tracking-wider cyber-pulse">
              Scanning...
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="sm:col-span-2">
            <input
              type="text"
              placeholder="GME, AMC, BBBY, SPRT..."
              value={scanForm.symbols}
              onChange={(e) =>
                setScanForm((prev) => ({ ...prev, symbols: e.target.value }))
              }
            />
          </div>
          <input
            type="text"
            placeholder="Start date"
            value={scanForm.start_date}
            onChange={(e) =>
              setScanForm((prev) => ({ ...prev, start_date: e.target.value }))
            }
          />
          <input
            type="number"
            placeholder="Min 3d return %"
            value={scanForm.min_return_3d_pct}
            onChange={(e) =>
              setScanForm((prev) => ({
                ...prev,
                min_return_3d_pct: e.target.value,
              }))
            }
          />
        </div>

        <div className="mt-3 flex items-center gap-2 flex-wrap">
          <Button onClick={handleScan} loading={scanning} size="sm">
            Scan Symbols
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleEnrich}
            loading={enriching}
          >
            Enrich All
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleClassify}
            loading={classifying}
          >
            Classify All
          </Button>
        </div>

        {scanResult && (
          <div className="mt-3 text-[0.7rem] text-neutral-400 tracking-wide font-mono">
            {scanResult}
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-[0.6rem] uppercase tracking-[0.15em] text-neutral-600">
          Filter:
        </span>
        <select
          value={labelFilter}
          onChange={(e) => setLabelFilter(e.target.value)}
          className="w-auto text-[0.75rem]"
        >
          <option value="">All labels</option>
          <option value="A">Label A (500%+)</option>
          <option value="B">Label B (1000%+)</option>
        </select>
        <select
          value={bucketFilter}
          onChange={(e) => setBucketFilter(e.target.value)}
          className="w-auto text-[0.75rem]"
        >
          <option value="">All buckets</option>
          {buckets.map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
        <span className="text-[0.6rem] text-neutral-700">
          {events.length} events shown
        </span>
      </div>

      {/* Bucket distribution */}
      {stats && Object.keys(stats.bucket_distribution).length > 0 && (
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Taxonomy Distribution
          </h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.bucket_distribution)
              .sort(([, a], [, b]) => b - a)
              .map(([bucket, count]) => (
                <button
                  key={bucket}
                  onClick={() =>
                    setBucketFilter(bucketFilter === bucket ? "" : bucket)
                  }
                  className={`px-3 py-1.5 text-[0.65rem] uppercase tracking-wider border transition-all ${
                    bucketFilter === bucket
                      ? "border-white text-white bg-white/5"
                      : "border-neutral-800 text-neutral-500 hover:border-neutral-600"
                  }`}
                >
                  {bucket}{" "}
                  <span className="text-neutral-600 ml-1">{count}</span>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Events table */}
      {events.length === 0 ? (
        <EmptyState
          title="No dislocation events"
          description="Run a scan or build a universe to discover extreme price dislocations."
        />
      ) : (
        <div className="border border-neutral-800 bg-neutral-950 relative overflow-x-auto">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <table>
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Date</th>
                <th>3d Return</th>
                <th>1d Return</th>
                <th>Price Start</th>
                <th>Price Peak</th>
                <th>Vol Ratio</th>
                <th>Short %</th>
                <th>Bucket</th>
                <th>Cont.</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>
                    <span className="font-bold text-white text-[0.8rem]">
                      {event.symbol}
                    </span>
                    {event.label_b === 1 && (
                      <span className="ml-1.5 text-[0.55rem] text-neutral-600 border border-neutral-700 px-1">
                        1000%+
                      </span>
                    )}
                  </td>
                  <td className="text-neutral-500 text-[0.75rem]">
                    {event.event_start_date?.split("T")[0]}
                  </td>
                  <td className="text-white font-bold">
                    {formatPercent(event.return_3d_pct)}
                  </td>
                  <td className="text-neutral-400">
                    {event.return_1d_pct != null
                      ? formatPercent(event.return_1d_pct)
                      : "--"}
                  </td>
                  <td className="text-neutral-500">
                    ${formatNumber(event.price_start, { maximumFractionDigits: 2 })}
                  </td>
                  <td className="text-neutral-400">
                    ${formatNumber(event.price_peak, { maximumFractionDigits: 2 })}
                  </td>
                  <td className="text-neutral-500">
                    {event.volume_ratio != null
                      ? formatNumber(event.volume_ratio, { maximumFractionDigits: 1 })
                      : "--"}
                  </td>
                  <td className="text-neutral-500">
                    {event.short_pct_float != null
                      ? formatPercent(event.short_pct_float)
                      : "--"}
                  </td>
                  <td>
                    {event.taxonomy_bucket ? (
                      <span className="qp-badge">{event.taxonomy_bucket}</span>
                    ) : (
                      <span className="text-neutral-700">--</span>
                    )}
                  </td>
                  <td>
                    {event.day_after_continuation === 1 ? (
                      <span className="text-white text-[0.7rem]">YES</span>
                    ) : event.day_after_continuation === 0 ? (
                      <span className="text-neutral-600 text-[0.7rem]">NO</span>
                    ) : (
                      <span className="text-neutral-700">--</span>
                    )}
                  </td>
                  <td>
                    <Link
                      href={`/research/events/${event.id}`}
                      className="text-[0.65rem] uppercase tracking-wider text-neutral-600 hover:text-white transition-colors"
                    >
                      Detail
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Top symbols */}
      {stats && stats.top_symbols.length > 0 && (
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Top Symbols by Event Count
          </h2>
          <div className="flex flex-wrap gap-x-6 gap-y-2">
            {stats.top_symbols.map(({ symbol, count }) => (
              <div key={symbol} className="flex items-center gap-2">
                <span className="text-sm font-bold text-white">{symbol}</span>
                <span className="text-[0.65rem] text-neutral-600">{count}</span>
                <div
                  className="h-1 bg-white/20"
                  style={{
                    width: `${Math.min((count / (stats.top_symbols[0]?.count || 1)) * 60, 60)}px`,
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
