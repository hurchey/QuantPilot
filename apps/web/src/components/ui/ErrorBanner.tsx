"use client";

import React from "react";

type ErrorBannerProps = {
  title?: string;
  message?: string;
  error?: string;
  onDismissAction?: () => void;
  className?: string;
};

export default function ErrorBanner({
  title = "Error",
  message,
  error,
  onDismissAction,
  className = "",
}: ErrorBannerProps) {
  const text = message ?? error ?? "Something went wrong.";

  return (
    <div
      role="alert"
      aria-live="polite"
      className={`rounded-xl border border-red-800/70 bg-red-950/30 px-4 py-3 text-red-200 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold">{title}</p>
          <p className="mt-1 text-sm text-red-200/90 whitespace-pre-wrap break-words">
            {text}
          </p>
        </div>

        {onDismissAction ? (
          <button
            type="button"
            onClick={onDismissAction}
            className="shrink-0 rounded-md border border-red-700 px-2 py-1 text-xs hover:bg-red-900/40"
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}