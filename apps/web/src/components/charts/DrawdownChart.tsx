// apps/web/src/components/charts/DrawdownChart.tsx
"use client";

import React, { useMemo } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

type RawDrawdownPoint = {
  timestamp?: string;
  date?: string;
  time?: string;
  drawdown_pct?: number | string;
  drawdown?: number | string;
  value?: number | string;
  [key: string]: unknown;
};

type DrawdownChartProps = {
  data: RawDrawdownPoint[];
  height?: number;
};

type ChartPoint = {
  x: string;
  drawdownPct: number;
};

function toNumber(value: unknown): number | null {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function formatTickLabel(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

function normalizeDrawdownPct(raw: number): number {
  // Accepts either:
  // - positive % (e.g. 12.5)
  // - negative % (e.g. -12.5)
  // - ratios (e.g. 0.125 or -0.125)
  let v = raw;

  if (Math.abs(v) <= 1) {
    v = v * 100;
  }

  // drawdown should display as negative
  if (v > 0) v = -v;

  return v;
}

export default function DrawdownChart({
  data,
  height = 280,
}: DrawdownChartProps) {
  const chartData = useMemo<ChartPoint[]>(() => {
    return (data ?? [])
      .map((p) => {
        const x =
          String(p.timestamp ?? p.date ?? p.time ?? "").trim() || "Unknown";

        const raw =
          toNumber(p.drawdown_pct) ?? toNumber(p.drawdown) ?? toNumber(p.value);

        if (raw === null) return null;

        return {
          x,
          drawdownPct: normalizeDrawdownPct(raw),
        };
      })
      .filter((p): p is ChartPoint => p !== null);
  }, [data]);

  if (!chartData.length) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">
        No drawdown data available.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <AreaChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            tickFormatter={formatTickLabel}
            minTickGap={24}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <YAxis
            width={70}
            tickFormatter={(v) => `${Number(v).toFixed(0)}%`}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <Tooltip
            formatter={(value: number | undefined) => {
                const safeValue = value ?? 0; // Provide a default value
                return [`${Number(safeValue).toFixed(2)}%`, "Drawdown"];
            }}
            labelFormatter={(label) => `Time: ${String(label)}`}
          />
          <Area
            type="monotone"
            dataKey="drawdownPct"
            stroke="#f87171"
            fill="#7f1d1d"
            fillOpacity={0.35}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}