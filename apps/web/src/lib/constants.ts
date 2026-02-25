// apps/web/src/lib/constants.ts

export const APP_NAME = "QuantPilot";

export const ROUTES = {
  home: "/",
  login: "/auth/login",
  register: "/auth/register",
  dashboard: "/dashboard",
  strategies: "/strategies",
  data: "/data",
  backtests: "/backtests",
} as const;

export const API_CONFIG = {
  baseUrl:
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
    "http://localhost:3000",
  requestTimeoutMs: 20_000,
} as const;

export const UI_DEFAULTS = {
  dashboardEquityPreviewPoints: 25,
  recentRunsPreviewCount: 10,
  tablePageSize: 25,
  currencyCode: "USD",
} as const;

export const TIMEFRAME_OPTIONS = [
  "1m",
  "5m",
  "15m",
  "30m",
  "1h",
  "4h",
  "1d",
  "1wk",
] as const;

export const STRATEGY_TYPES = [
  {
    value: "sma_crossover",
    label: "SMA Crossover",
    description: "Fast/slow moving-average crossover trend strategy",
  },
] as const;

export const DASHBOARD_SECTIONS = {
  summary: "Summary",
  risk: "Risk",
  performance: "Performance",
} as const;

export const AUTH_ERROR_HINTS = [
  "not authenticated",
  "unauthorized",
  "forbidden",
  "invalid token",
  "login required",
] as const;