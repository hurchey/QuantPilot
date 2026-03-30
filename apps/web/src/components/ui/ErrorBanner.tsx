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
  title = "ERROR",
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
      className={`border border-red-900 bg-red-950/20 px-4 py-3 text-red-400 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[0.65rem] font-bold uppercase tracking-[0.12em]">
            {title}
          </p>
          <p className="mt-1 text-xs text-red-400/80 whitespace-pre-wrap break-words">
            {text}
          </p>
        </div>

        {onDismissAction ? (
          <button
            type="button"
            onClick={onDismissAction}
            className="shrink-0 border border-red-800 px-2 py-1 text-[0.6rem] uppercase tracking-wider hover:bg-red-900/30 transition-colors"
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  );
}
