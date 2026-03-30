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
    "inline-flex items-center justify-center border font-semibold uppercase tracking-[0.08em] transition-all disabled:opacity-40 disabled:cursor-not-allowed";
  const sizes = {
    sm: "px-3 py-1.5 text-[0.65rem]",
    md: "px-4 py-2 text-[0.7rem]",
  } as const;

  const variants = {
    primary: "bg-white text-black border-white hover:bg-neutral-200 hover:shadow-[0_0_12px_rgba(255,255,255,0.1)]",
    secondary:
      "bg-transparent text-neutral-300 border-neutral-700 hover:border-white hover:text-white",
    danger:
      "bg-transparent text-red-400 border-red-800 hover:bg-red-950/30 hover:border-red-600",
    ghost: "bg-transparent text-neutral-500 border-transparent hover:text-white hover:bg-neutral-900",
  } as const;

  return (
    <button
      className={cx(base, sizes[size], variants[variant], className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "LOADING..." : children}
    </button>
  );
}
