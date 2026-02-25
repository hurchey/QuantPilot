// apps/web/src/hooks/useStrategies.ts
"use client";

import { useCallback, useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") || "http://localhost:3000";

export type Strategy = {
  id: number;
  name: string;
  symbol?: string;
  timeframe?: string;
  strategy_type?: string;
  params_json?: Record<string, unknown>;
  is_active?: boolean;
  created_at?: string;
};

type CreateStrategyInput = {
  name: string;
  symbol: string;
  timeframe: string;
  strategy_type: string;
  params_json?: Record<string, unknown>;
};

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return res.json();
}

export function useStrategies() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchJson<Strategy[]>("/quant/strategies");
      setStrategies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load strategies");
    } finally {
      setLoading(false);
    }
  }, []);

  const createStrategy = useCallback(async (payload: CreateStrategyInput) => {
    setCreating(true);
    setCreateError("");
    try {
      const created = await fetchJson<Strategy>("/quant/strategies", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setStrategies((prev) => [created, ...prev]);
      return created;
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to create strategy";
      setCreateError(msg);
      throw err;
    } finally {
      setCreating(false);
    }
  }, []);

  const toggleStrategyActive = useCallback(async (strategyId: number, isActive: boolean) => {
    const updated = await fetchJson<Strategy>(`/quant/strategies/${strategyId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });

    setStrategies((prev) =>
      prev.map((s) => (s.id === strategyId ? updated : s))
    );

    return updated;
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    strategies,
    loading,
    error,

    refresh,

    creating,
    createError,
    createStrategy,

    toggleStrategyActive,
  };
}