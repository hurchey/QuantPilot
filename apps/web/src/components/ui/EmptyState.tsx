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
      className={`border border-neutral-800 bg-neutral-950/50 p-6 text-center ${className}`}
    >
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral-400">
        {title}
      </div>

      {description ? (
        <p className="mt-2 text-[0.75rem] text-neutral-600">{description}</p>
      ) : null}

      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 border border-neutral-700 bg-transparent px-3 py-2 text-[0.65rem] uppercase tracking-wider text-neutral-400 hover:border-white hover:text-white transition-all"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}
