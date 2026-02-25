// src/lib/api.ts
const DEFAULT_API_BASE_URL = "http://localhost:3000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || DEFAULT_API_BASE_URL;

const TOKEN_KEY = "qp_access_token";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

function buildUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

type ApiFetchOptions = RequestInit & {
  skipAuth?: boolean;
};

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { skipAuth = false, headers, body, ...rest } = options;

  const mergedHeaders = new Headers(headers || {});
  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;

  if (!skipAuth) {
    const token = getAuthToken();
    if (token) {
      mergedHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  if (!isFormData && body && !mergedHeaders.has("Content-Type")) {
    mergedHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(buildUrl(path), {
    ...rest,
    headers: mergedHeaders,
    body,
  });

  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  const payload = isJson ? await response.json().catch(() => null) : await response.text().catch(() => "");

  if (!response.ok) {
    const message =
      (payload &&
        typeof payload === "object" &&
        ("detail" in payload ? String((payload as any).detail) : "")) ||
      (typeof payload === "string" ? payload : "") ||
      `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload as T;
}

// Optional convenience helpers
export function apiGet<T = unknown>(path: string, options: ApiFetchOptions = {}) {
  return apiFetch<T>(path, { ...options, method: "GET" });
}

export function apiPost<T = unknown>(
  path: string,
  data?: unknown,
  options: ApiFetchOptions = {}
) {
  const body =
    data instanceof FormData ? data : data !== undefined ? JSON.stringify(data) : undefined;
  return apiFetch<T>(path, { ...options, method: "POST", body });
}

export function apiDelete<T = unknown>(path: string, options: ApiFetchOptions = {}) {
  return apiFetch<T>(path, { ...options, method: "DELETE" });
}