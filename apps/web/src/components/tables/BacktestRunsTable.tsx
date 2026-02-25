"use client";

import React from "react";

type BacktestRun = {
  id: number;
  strategy_id?: number;
  status?: string;
  created_at?: string;
  metrics_json?: Record<string, unknown>;
  [key: string]: unknown;
};

type BacktestRunsTableProps = {
  runs: BacktestRun[];
  selectedRunId?: number | null;
  onSelectRunAction?: (run: BacktestRun) => void;
  className?: string;
};

function formatDate(value?: string): string {
  if (!value) return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

function fmt(value: unknown, digits = 2): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "-";
}

export default function BacktestRunsTable({
  runs,
  selectedRunId = null,
  onSelectRunAction,
  className = "",
}: BacktestRunsTableProps) {
  if (!runs?.length) {
    return (
      <div className={`text-sm text-slate-400 ${className}`}>
        No backtest runs yet.
      </div>
    );
  }

  return (
    <div className={`overflow-auto ${className}`}>
      <table>
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Status</th>
            <th>Strategy</th>
            <th>Return</th>
            <th>Sharpe</th>
            <th>Created</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => {
            const metrics = run.metrics_json ?? {};
            const totalReturn =
              metrics["total_return_pct"] ?? metrics["return_pct"] ?? metrics["total_return"];
            const sharpe = metrics["sharpe_ratio"] ?? metrics["sharpe"];

            const isSelected = selectedRunId === run.id;

            return (
              <tr
                key={run.id}
                onClick={() => onSelectRunAction?.(run)}
                className={onSelectRunAction ? "cursor-pointer" : ""}
                style={{
                  background: isSelected ? "rgba(59,130,246,0.08)" : undefined,
                }}
              >
                <td className="font-medium">#{run.id}</td>
                <td>
                  <span
                    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${
                      run.status === "completed"
                        ? "border-emerald-700 text-emerald-300"
                        : run.status === "failed"
                        ? "border-red-700 text-red-300"
                        : "border-slate-700 text-slate-300"
                    }`}
                  >
                    {run.status ?? "unknown"}
                  </span>
                </td>
                <td>{run.strategy_id ?? "-"}</td>
                <td>{totalReturn !== undefined ? `${fmt(totalReturn)}%` : "-"}</td>
                <td>{fmt(sharpe)}</td>
                <td>{formatDate(run.created_at)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}