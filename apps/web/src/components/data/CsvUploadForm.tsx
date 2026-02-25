"use client";

import React, { useMemo, useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";

type CsvUploadResponse = {
  message?: string;
  rows_inserted?: number;
  symbol?: string;
  timeframe?: string;
  [key: string]: unknown;
};

type CsvUploadFormProps = {
  apiPath?: string; // default: /quant/data/upload
  defaultSymbol?: string;
  defaultTimeframe?: string;
  onUploadedAction?: (result: CsvUploadResponse) => void;
  className?: string;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:3000";

export default function CsvUploadForm({
  apiPath = "/quant/data/upload",
  defaultSymbol = "SPY",
  defaultTimeframe = "1d",
  onUploadedAction,
  className = "",
}: CsvUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [timeframe, setTimeframe] = useState(defaultTimeframe);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const acceptedText = useMemo(
    () => "CSV files only. Typical columns: timestamp, open, high, low, close, volume.",
    []
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    setError("");
    setSuccessMessage("");

    if (!file) {
      setError("Please choose a CSV file to upload.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Only .csv files are supported.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("symbol", symbol.trim());
      formData.append("timeframe", timeframe.trim());

      const res = await fetch(`${API_BASE}${apiPath}`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      const contentType = res.headers.get("content-type") || "";
      const data = contentType.includes("application/json")
        ? ((await res.json()) as CsvUploadResponse)
        : ({ message: await res.text() } as CsvUploadResponse);

      if (!res.ok) {
        throw new Error(
          data?.message || `Upload failed with status ${res.status}`
        );
      }

      const rowsInserted =
        typeof data.rows_inserted === "number" ? ` (${data.rows_inserted} rows)` : "";
      setSuccessMessage(data.message || `Upload successful${rowsInserted}`);

      setFile(null);
      // reset file input manually by form reset if needed
      (e.target as HTMLFormElement).reset();

      onUploadedAction?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={`qp-panel space-y-4 ${className}`}>
      <div className="qp-panel-header">
        <h2>Upload Market Data (CSV)</h2>
      </div>

      <p className="text-sm text-slate-400">{acceptedText}</p>

      {error ? (
        <ErrorBanner title="Upload Error" message={error} onDismissAction={() => setError("")} />
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
            required
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-slate-300">Timeframe</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            required
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="4h">4h</option>
            <option value="1d">1d</option>
            <option value="1wk">1wk</option>
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm text-slate-300">CSV File</label>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          required
        />
        {file ? (
          <p className="mt-2 text-xs text-slate-400">
            Selected: <span className="text-slate-200">{file.name}</span>
          </p>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        <button type="submit" className="qp-btn qp-btn-primary" disabled={loading}>
          {loading ? "Uploading..." : "Upload CSV"}
        </button>

        {loading ? <LoadingSpinner size="sm" text="Processing file..." /> : null}
      </div>
    </form>
  );
}