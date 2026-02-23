const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is not set");
}

type QueryValue = string | number | boolean | null | undefined;
type QueryParams = Record<string, QueryValue>;

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

type ApiOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
  query?: QueryParams;
};

function buildUrl(path: string, query?: QueryParams): string {
  const url = new URL(path, API_URL);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === null || value === undefined) continue;
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

function getErrorMessage(data: unknown, fallback = "Request failed"): string {
  if (!data) return fallback;

  if (typeof data === "string") return data;

  if (typeof data === "object" && data !== null) {
    // FastAPI commonly returns { detail: "..." } or { detail: [...] }
    const maybeDetail = (data as { detail?: unknown }).detail;

    if (typeof maybeDetail === "string") return maybeDetail;

    if (Array.isArray(maybeDetail)) {
      // Validation errors can be arrays; stringify a readable version
      return maybeDetail
        .map((item) => {
          if (typeof item === "string") return item;
          if (typeof item === "object" && item !== null) {
            const msg = (item as { msg?: unknown }).msg;
            return typeof msg === "string" ? msg : JSON.stringify(item);
          }
          return String(item);
        })
        .join(", ");
    }
  }

  return fallback;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { query, headers: incomingHeaders, ...rest } = options;

  const headers = new Headers(incomingHeaders);

  // Set defaults
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const hasBody = rest.body !== undefined;
  const isFormData = typeof FormData !== "undefined" && rest.body instanceof FormData;

  // Only set JSON content type when appropriate
  if (hasBody && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(buildUrl(path, query), {
    ...rest,
    headers,
    credentials: "include", // important for HttpOnly cookie auth
  });

  // Handle empty responses (e.g. 204)
  if (res.status === 204) {
    return undefined as T;
  }

  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  let data: unknown;
  try {
    data = isJson ? await res.json() : await res.text();
  } catch {
    data = null;
  }

  if (!res.ok) {
    throw new ApiError(getErrorMessage(data), res.status, data);
  }

  return data as T;
}

// Optional convenience wrappers
export const api = {
  get: <T>(path: string, query?: QueryParams, options?: Omit<ApiOptions, "query" | "method">) =>
    apiFetch<T>(path, { ...options, method: "GET", query }),

  post: <T>(
    path: string,
    body?: unknown,
    options?: Omit<ApiOptions, "body" | "method">
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: "POST",
      body:
        body instanceof FormData || typeof body === "string" ? body : body !== undefined ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(
    path: string,
    body?: unknown,
    options?: Omit<ApiOptions, "body" | "method">
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: "PATCH",
      body:
        body instanceof FormData || typeof body === "string" ? body : body !== undefined ? JSON.stringify(body) : undefined,
    }),

  put: <T>(
    path: string,
    body?: unknown,
    options?: Omit<ApiOptions, "body" | "method">
  ) =>
    apiFetch<T>(path, {
      ...options,
      method: "PUT",
      body:
        body instanceof FormData || typeof body === "string" ? body : body !== undefined ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, options?: Omit<ApiOptions, "method">) =>
    apiFetch<T>(path, { ...options, method: "DELETE" }),
};