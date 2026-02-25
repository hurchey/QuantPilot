// apps/web/src/components/charts/EquityCurveChart.tsx
"use client";

import React, { useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

type RawEquityPoint = {
  timestamp?: string;
  date?: string;
  time?: string;
  equity?: number | string;
  value?: number | string;
  close?: number | string;
  [key: string]: unknown;
};

type EquityCurveChartProps = {
  data: RawEquityPoint[];
  height?: number;
};

type ChartPoint = {
  x: string;
  equity: number;
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

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function EquityCurveChart({
  data,
  height = 280,
}: EquityCurveChartProps) {
  const chartData = useMemo<ChartPoint[]>(() => {
    return (data ?? [])
      .map((p) => {
        const x =
          String(p.timestamp ?? p.date ?? p.time ?? "").trim() || "Unknown";
        const equity =
          toNumber(p.equity) ?? toNumber(p.value) ?? toNumber(p.close);

        if (equity === null) return null;

        return { x, equity };
      })
      .filter((p): p is ChartPoint => p !== null);
  }, [data]);

  if (!chartData.length) {
    return (
      <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-4 text-sm text-slate-400">
        No equity curve data available.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="x"
            tickFormatter={formatTickLabel}
            minTickGap={24}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <YAxis
            width={80}
            tickFormatter={(v) => formatCurrency(Number(v))}
            tick={{ fill: "#94a3b8", fontSize: 11 }}
          />
          <Tooltip
            formatter={(value?: number) => value !== undefined ? [formatCurrency(value), "Equity"] : ["-", "Equity"]}
            labelFormatter={(label) => `Time: ${String(label)}`}
          />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}