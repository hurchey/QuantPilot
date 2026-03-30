"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorBanner from "@/components/ui/ErrorBanner";
import MetricCard from "@/components/ui/MetricCard";
import { formatNumber } from "@/lib/format";

type SeedEvent = {
  symbol: string;
  catalyst: string;
  date?: string;
};

type SeedListResponse = {
  total: number;
  catalysts: string[];
  events: SeedEvent[];
};

type BuildResult = {
  tickers_scanned: number;
  events_found: number;
  events_persisted: number;
  ticker_sources?: Record<string, number>;
  events_enriched?: number;
  events_classified?: number;
  errors: string[];
};

type FtdSignal = {
  SYMBOL?: string;
  symbol?: string;
  QUANTITY?: number;
  quantity?: number;
};

type FtdResponse = {
  total: number;
  symbols: FtdSignal[];
};

type UniverseScanForm = {
  universe: string;
  custom_symbols: string;
  start_date: string;
  min_return_3d_pct: string;
};

export default function UniverseBuilderPage() {
  const [seedList, setSeedList] = useState<SeedListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Build state
  const [building, setBuilding] = useState(false);
  const [buildResult, setBuildResult] = useState<BuildResult | null>(null);
  const [buildType, setBuildType] = useState<string>("");

  // Universe scan
  const [scanForm, setScanForm] = useState<UniverseScanForm>({
    universe: "sp500",
    custom_symbols: "",
    start_date: "2019-01-01",
    min_return_3d_pct: "500",
  });
  const [universeScanning, setUniverseScanning] = useState(false);

  // FTD signals
  const [ftdSignals, setFtdSignals] = useState<FtdSignal[]>([]);
  const [ftdLoading, setFtdLoading] = useState(false);
  const [ftdYear, setFtdYear] = useState("2024");
  const [ftdHalf, setFtdHalf] = useState("1");

  // Full pipeline
  const [fullForm, setFullForm] = useState({
    include_edgar: true,
    include_ftd: true,
    edgar_max_tickers: "100",
    enrich: true,
    classify: true,
  });

  useEffect(() => {
    async function load() {
      try {
        const seeds = await apiGet<SeedListResponse>("/quant/research/seed-list");
        setSeedList(seeds);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load seed list");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleBuildSeeds() {
    setBuilding(true);
    setBuildType("SEEDS");
    setBuildResult(null);
    try {
      const res = await apiPost<BuildResult>("/quant/research/build-seeds");
      setBuildResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Build from seeds failed");
    } finally {
      setBuilding(false);
    }
  }

  async function handleBuildEdgar() {
    setBuilding(true);
    setBuildType("EDGAR");
    setBuildResult(null);
    try {
      const res = await apiPost<BuildResult>(
        "/quant/research/build-edgar?max_tickers=100"
      );
      setBuildResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Build from EDGAR failed");
    } finally {
      setBuilding(false);
    }
  }

  async function handleBuildFtd() {
    setBuilding(true);
    setBuildType("FTD");
    setBuildResult(null);
    try {
      const res = await apiPost<BuildResult>("/quant/research/build-ftd");
      setBuildResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Build from FTD failed");
    } finally {
      setBuilding(false);
    }
  }

  async function handleBuildFull() {
    setBuilding(true);
    setBuildType("FULL PIPELINE");
    setBuildResult(null);
    try {
      const params = new URLSearchParams({
        include_edgar: String(fullForm.include_edgar),
        include_ftd: String(fullForm.include_ftd),
        edgar_max_tickers: fullForm.edgar_max_tickers,
        enrich: String(fullForm.enrich),
        classify: String(fullForm.classify),
      });
      const res = await apiPost<BuildResult>(
        `/quant/research/build-full?${params}`
      );
      setBuildResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Full pipeline failed");
    } finally {
      setBuilding(false);
    }
  }

  async function handleUniverseScan() {
    setUniverseScanning(true);
    setBuildResult(null);
    setBuildType("UNIVERSE SCAN");
    try {
      const body: Record<string, unknown> = {
        universe: scanForm.universe,
        start_date: scanForm.start_date,
        min_return_3d_pct: Number(scanForm.min_return_3d_pct),
      };
      if (scanForm.universe === "custom" && scanForm.custom_symbols) {
        body.custom_symbols = scanForm.custom_symbols
          .split(/[,\s]+/)
          .map((s) => s.trim().toUpperCase())
          .filter(Boolean);
      }
      const res = await apiPost<{
        total_symbols_scanned: number;
        total_events_found: number;
      }>("/quant/research/scan-universe", body);
      setBuildResult({
        tickers_scanned: res.total_symbols_scanned,
        events_found: res.total_events_found,
        events_persisted: res.total_events_found,
        errors: [],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Universe scan failed");
    } finally {
      setUniverseScanning(false);
    }
  }

  async function handleLoadFtd() {
    setFtdLoading(true);
    try {
      const res = await apiGet<FtdResponse>(
        `/quant/research/ftd-signals?year=${ftdYear}&half=${ftdHalf}`
      );
      setFtdSignals(res.symbols ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load FTD signals");
    } finally {
      setFtdLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="py-16 flex justify-center">
        <LoadingSpinner text="LOADING UNIVERSE BUILDER..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/research"
          className="text-[0.6rem] uppercase tracking-[0.15em] text-neutral-600 hover:text-white transition-colors"
        >
          &larr; Research Hub
        </Link>
        <h1 className="mt-2 text-lg font-bold tracking-[0.15em] uppercase text-white">
          Universe Builder
        </h1>
        <p className="text-[0.7rem] text-neutral-600 tracking-wide mt-1">
          Build dislocation datasets from seeds, SEC EDGAR, FTD signals, or full
          pipeline
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismissAction={() => setError(null)} />}

      {/* Build result banner */}
      {buildResult && (
        <div className="border border-neutral-700 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-600 to-transparent" />
          <div className="text-[0.65rem] uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Build Result // {buildType}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard
              label="Scanned"
              value={formatNumber(buildResult.tickers_scanned, { maximumFractionDigits: 0 })}
            />
            <MetricCard
              label="Events Found"
              value={formatNumber(buildResult.events_found, { maximumFractionDigits: 0 })}
            />
            <MetricCard
              label="Persisted"
              value={formatNumber(buildResult.events_persisted, { maximumFractionDigits: 0 })}
            />
            {buildResult.events_enriched != null && (
              <MetricCard
                label="Enriched"
                value={formatNumber(buildResult.events_enriched, { maximumFractionDigits: 0 })}
              />
            )}
          </div>
          {buildResult.errors.length > 0 && (
            <div className="mt-3 max-h-32 overflow-y-auto">
              <div className="text-[0.6rem] uppercase tracking-wider text-red-500 mb-1">
                Errors ({buildResult.errors.length})
              </div>
              {buildResult.errors.slice(0, 10).map((e, i) => (
                <div key={i} className="text-[0.7rem] text-neutral-600 truncate">
                  {e}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Building indicator */}
      {building && (
        <div className="flex items-center gap-3 py-2">
          <LoadingSpinner size="sm" />
          <span className="text-[0.7rem] uppercase tracking-wider text-neutral-500 cyber-pulse">
            Building {buildType}...
          </span>
        </div>
      )}

      {/* Quick build actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Seeds */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            Seed List
          </h2>
          <p className="text-[0.65rem] text-neutral-700 mb-3">
            {seedList?.total ?? 0} curated extreme movers with known catalysts
          </p>
          <Button onClick={handleBuildSeeds} loading={building && buildType === "SEEDS"} size="sm">
            Build from Seeds
          </Button>

          {seedList && seedList.events.length > 0 && (
            <div className="mt-4 max-h-48 overflow-y-auto">
              <table>
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Catalyst</th>
                  </tr>
                </thead>
                <tbody>
                  {seedList.events.map((s, i) => (
                    <tr key={i}>
                      <td className="text-white font-bold text-[0.75rem]">
                        {s.symbol}
                      </td>
                      <td className="text-neutral-500 text-[0.7rem]">
                        {s.catalyst}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* EDGAR */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            SEC EDGAR Universe
          </h2>
          <p className="text-[0.65rem] text-neutral-700 mb-3">
            Scan the full EDGAR ticker universe. Slow but comprehensive.
          </p>
          <Button
            onClick={handleBuildEdgar}
            loading={building && buildType === "EDGAR"}
            size="sm"
            variant="secondary"
          >
            Build from EDGAR (100 tickers)
          </Button>
        </div>

        {/* FTD Signals */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            FTD Signals
          </h2>
          <p className="text-[0.65rem] text-neutral-700 mb-3">
            Symbols with high Failures-to-Deliver — prime squeeze candidates
          </p>
          <div className="flex items-center gap-2 mb-3">
            <input
              type="number"
              value={ftdYear}
              onChange={(e) => setFtdYear(e.target.value)}
              className="w-20 text-[0.75rem]"
              placeholder="Year"
            />
            <select
              value={ftdHalf}
              onChange={(e) => setFtdHalf(e.target.value)}
              className="w-auto text-[0.75rem]"
            >
              <option value="1">H1</option>
              <option value="2">H2</option>
            </select>
            <Button variant="secondary" size="sm" onClick={handleLoadFtd} loading={ftdLoading}>
              Load FTD
            </Button>
            <Button
              size="sm"
              onClick={handleBuildFtd}
              loading={building && buildType === "FTD"}
            >
              Build from FTD
            </Button>
          </div>
          {ftdSignals.length > 0 && (
            <div className="max-h-40 overflow-y-auto">
              <div className="flex flex-wrap gap-2">
                {ftdSignals.slice(0, 40).map((s, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 text-[0.65rem] border border-neutral-800 text-neutral-400"
                  >
                    {s.SYMBOL || s.symbol}
                  </span>
                ))}
                {ftdSignals.length > 40 && (
                  <span className="text-[0.6rem] text-neutral-600">
                    +{ftdSignals.length - 40} more
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Universe scan */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            Universe Scan
          </h2>
          <p className="text-[0.65rem] text-neutral-700 mb-3">
            Scan a predefined universe (S&P 500, Russell 2000, etc.)
          </p>
          <div className="grid grid-cols-2 gap-2 mb-3">
            <select
              value={scanForm.universe}
              onChange={(e) =>
                setScanForm((prev) => ({ ...prev, universe: e.target.value }))
              }
              className="text-[0.75rem]"
            >
              <option value="sp500">S&P 500</option>
              <option value="russell2000">Russell 2000</option>
              <option value="all_us">All US</option>
              <option value="custom">Custom</option>
            </select>
            <input
              type="text"
              value={scanForm.start_date}
              onChange={(e) =>
                setScanForm((prev) => ({ ...prev, start_date: e.target.value }))
              }
              className="text-[0.75rem]"
              placeholder="Start date"
            />
          </div>
          {scanForm.universe === "custom" && (
            <input
              type="text"
              value={scanForm.custom_symbols}
              onChange={(e) =>
                setScanForm((prev) => ({
                  ...prev,
                  custom_symbols: e.target.value,
                }))
              }
              className="mb-3 text-[0.75rem]"
              placeholder="AAPL, TSLA, GME..."
            />
          )}
          <Button
            onClick={handleUniverseScan}
            loading={universeScanning}
            size="sm"
          >
            Scan Universe
          </Button>
        </div>
      </div>

      {/* Full pipeline */}
      <div className="border border-neutral-700 bg-neutral-950 p-4 relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-600 to-transparent" />
        <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-400 mb-1">
          Full Pipeline
        </h2>
        <p className="text-[0.65rem] text-neutral-600 mb-4">
          Seeds + EDGAR + FTD signals &rarr; enrich &rarr; classify. End-to-end
          dataset build.
        </p>

        <div className="flex items-center gap-4 flex-wrap mb-4">
          <label className="flex items-center gap-1.5 text-[0.7rem] text-neutral-400">
            <input
              type="checkbox"
              checked={fullForm.include_edgar}
              onChange={(e) =>
                setFullForm((prev) => ({ ...prev, include_edgar: e.target.checked }))
              }
              className="w-3.5 h-3.5"
            />
            Include EDGAR
          </label>
          <label className="flex items-center gap-1.5 text-[0.7rem] text-neutral-400">
            <input
              type="checkbox"
              checked={fullForm.include_ftd}
              onChange={(e) =>
                setFullForm((prev) => ({ ...prev, include_ftd: e.target.checked }))
              }
              className="w-3.5 h-3.5"
            />
            Include FTD
          </label>
          <label className="flex items-center gap-1.5 text-[0.7rem] text-neutral-400">
            <input
              type="checkbox"
              checked={fullForm.enrich}
              onChange={(e) =>
                setFullForm((prev) => ({ ...prev, enrich: e.target.checked }))
              }
              className="w-3.5 h-3.5"
            />
            Enrich
          </label>
          <label className="flex items-center gap-1.5 text-[0.7rem] text-neutral-400">
            <input
              type="checkbox"
              checked={fullForm.classify}
              onChange={(e) =>
                setFullForm((prev) => ({ ...prev, classify: e.target.checked }))
              }
              className="w-3.5 h-3.5"
            />
            Classify
          </label>
          <div className="flex items-center gap-1.5">
            <span className="text-[0.65rem] text-neutral-600">EDGAR limit:</span>
            <input
              type="number"
              value={fullForm.edgar_max_tickers}
              onChange={(e) =>
                setFullForm((prev) => ({
                  ...prev,
                  edgar_max_tickers: e.target.value,
                }))
              }
              className="w-20 text-[0.75rem]"
            />
          </div>
        </div>

        <Button
          onClick={handleBuildFull}
          loading={building && buildType === "FULL PIPELINE"}
        >
          Execute Full Pipeline
        </Button>
      </div>
    </div>
  );
}
