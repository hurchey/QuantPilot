"use client";

import React, { useState } from "react";
import ErrorBanner from "@/components/ui/ErrorBanner";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { apiPost } from "@/lib/api";

type ParquetUploadFormProps = {
  onSuccess?: () => void;
  className?: string;
};

export default function ParquetUploadForm({ onSuccess, className = "" }: ParquetUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [symbol, setSymbol] = useState("SPY");
  const [timeframe, setTimeframe] = useState("1d");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSuccessMessage("");

    if (!file) {
      setError("Please choose a Parquet file.");
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("symbol", symbol.trim());
      formData.append("timeframe", timeframe.trim());

      const data = await apiPost<{ rows_inserted?: number; symbol?: string; timeframe?: string }>(
        "/quant/data/upload-parquet",
        formData
      );
      if (!data) throw new Error("No response");
      setSuccessMessage(
        `Uploaded ${data.rows_inserted ?? 0} rows for ${data.symbol ?? symbol} (${data.timeframe ?? timeframe}).`
      );
      setFile(null);
      (e.target as HTMLFormElement).reset();
      onSuccess?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`}>
      <p className="text-sm text-slate-400">
        Parquet files with columns: timestamp, open, high, low, close, volume (aliases: ts/o/h/l/c/v).
      </p>

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
            <option value="4h">4h</option>
            <option value="1d">1d</option>
            <option value="1wk">1wk</option>
          </select>
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm text-slate-300">Parquet file</label>
        <input
          type="file"
          accept=".parquet,.pq"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          required
          className="w-full text-sm text-slate-300 file:mr-2 file:rounded-lg file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-slate-100"
        />
      </div>

      <button
        type="submit"
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-slate-100 hover:bg-slate-600 disabled:opacity-50"
      >
        {loading ? (
          <>
            <LoadingSpinner size="sm" />
            Uploading...
          </>
        ) : (
          "Upload Parquet"
        )}
      </button>
    </form>
  );
}
