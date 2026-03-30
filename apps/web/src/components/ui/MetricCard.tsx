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
      <div className="text-[0.6rem] font-semibold uppercase tracking-[0.15em] text-neutral-600">
        {displayLabel}
      </div>

      <div className="mt-2 text-xl font-bold text-white tracking-wide break-words">
        {value}
      </div>

      {subvalue ? (
        <div className="mt-1 text-xs text-neutral-500">{subvalue}</div>
      ) : null}

      {helperText ? (
        <div className="mt-2 text-[0.65rem] text-neutral-700">{helperText}</div>
      ) : null}
    </div>
  );
}
