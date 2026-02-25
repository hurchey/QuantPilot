// apps/web/src/components/ui/MetricCard.tsx
import React from "react";

type MetricCardProps = {
  label?: string;
  title?: string;
  value: React.ReactNode;
  subvalue?: React.ReactNode;
  helperText?: React.ReactNode;
  className?: string;
};

export default function MetricCard({
  label,
  title,
  value,
  subvalue,
  helperText,
  className = "",
}: MetricCardProps) {
  const displayLabel = label ?? title ?? "Metric";

  return (
    <div className={`qp-panel ${className}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {displayLabel}
      </div>

      <div className="mt-2 text-2xl font-semibold text-slate-100 break-words">
        {value}
      </div>

      {subvalue ? (
        <div className="mt-1 text-sm text-slate-300">{subvalue}</div>
      ) : null}

      {helperText ? (
        <div className="mt-2 text-xs text-slate-500">{helperText}</div>
      ) : null}
    </div>
  );
}