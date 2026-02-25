// apps/web/src/hooks/useAsyncAction.ts
"use client";

import { useCallback, useState } from "react";
import { getErrorMessage } from "@/lib/format";

type AsyncFn<TArgs extends unknown[], TResult> = (...args: TArgs) => Promise<TResult>;

export function useAsyncAction<TArgs extends unknown[], TResult>(
  fn: AsyncFn<TArgs, TResult>
) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const run = useCallback(
    async (...args: TArgs): Promise<TResult | null> => {
      setLoading(true);
      setError("");
      try {
        const result = await fn(...args);
        return result;
      } catch (err) {
        setError(getErrorMessage(err));
        return null;
      } finally {
        setLoading(false);
      }
    },
    [fn]
  );

  const clearError = useCallback(() => setError(""), []);

  return {
    loading,
    error,
    run,
    clearError,
  };
}