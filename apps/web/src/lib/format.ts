// apps/web/src/lib/format.ts

import { UI_DEFAULTS } from "@/lib/constants";

export function formatKeyLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatNumber(
  value: unknown,
  options?: { maximumFractionDigits?: number; minimumFractionDigits?: number }
): string {
  const num = Number(value);

  if (!Number.isFinite(num)) return "-";

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: options?.maximumFractionDigits ?? 4,
    minimumFractionDigits: options?.minimumFractionDigits ?? 0,
  }).format(num);
}

export function formatInteger(value: unknown): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(num);
}

export function formatPercent(
  value: unknown,
  options?: { inputIsRatio?: boolean; digits?: number }
): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";

  const digits = options?.digits ?? 2;

  // Many backtest APIs return pct as 12.34 rather than 0.1234.
  // Set inputIsRatio=true if you know your backend returns ratios.
  const pct = options?.inputIsRatio ? num * 100 : num;
  return `${pct.toFixed(digits)}%`;
}

export function formatCurrency(
  value: unknown,
  options?: { digits?: number; currency?: string }
): string {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: options?.currency ?? UI_DEFAULTS.currencyCode,
    maximumFractionDigits: options?.digits ?? 2,
    minimumFractionDigits: options?.digits ?? 2,
  }).format(num);
}

export function formatDateTime(value: unknown): string {
  if (typeof value !== "string" || !value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatShortDate(value: unknown): string {
  if (typeof value !== "string" || !value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}

export function formatMaybeJson(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function truncateMiddle(value: string, max = 24): string {
  if (value.length <= max) return value;
  const left = Math.ceil((max - 3) / 2);
  const right = Math.floor((max - 3) / 2);
  return `${value.slice(0, left)}...${value.slice(-right)}`;
}

export function isAuthErrorMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return [
    "not authenticated",
    "unauthorized",
    "forbidden",
    "invalid token",
    "login required",
  ].some((needle) => lower.includes(needle));
}

export function getErrorMessage(error: unknown, fallback = "Something went wrong"): string {
  if (error instanceof Error && error.message) return error.message;
  if (typeof error === "string" && error.trim()) return error;
  return fallback;
}