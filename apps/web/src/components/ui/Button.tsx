// apps/web/src/components/ui/Button.tsx
"use client";

import * as React from "react";

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  size?: "sm" | "md";
  loading?: boolean;
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-lg border font-medium transition-colors disabled:opacity-60 disabled:cursor-not-allowed";
  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
  } as const;

  const variants = {
    primary: "bg-slate-100 text-slate-900 border-slate-100 hover:bg-white",
    secondary:
      "bg-slate-900 text-slate-100 border-slate-700 hover:border-slate-500",
    danger:
      "bg-red-950/40 text-red-300 border-red-800 hover:bg-red-950/60 hover:border-red-700",
    ghost: "bg-transparent text-slate-300 border-transparent hover:bg-slate-800",
  } as const;

  return (
    <button
      className={cx(base, sizes[size], variants[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "Loading..." : children}
    </button>
  );
}