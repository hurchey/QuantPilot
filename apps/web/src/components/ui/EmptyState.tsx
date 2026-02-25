// apps/web/src/components/ui/EmptyState.tsx
import React from "react";

type EmptyStateProps = {
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
};

export default function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`rounded-xl border border-slate-800 bg-slate-950/50 p-6 text-center ${className}`}
    >
      <div className="text-sm font-semibold text-slate-200">{title}</div>

      {description ? (
        <p className="mt-2 text-sm text-slate-400">{description}</p>
      ) : null}

      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm hover:bg-slate-800"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}