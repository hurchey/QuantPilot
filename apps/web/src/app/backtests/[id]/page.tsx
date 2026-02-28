"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Redirect /backtests/[id] to /backtests.
 * Backtest detail is shown inline on the main backtests page.
 */
export default function BacktestDetailPage() {
  const router = useRouter();
  const params = useParams();

  useEffect(() => {
    router.replace("/backtests");
  }, [router, params]);

  return (
    <div className="flex min-h-[200px] items-center justify-center">
      <p className="text-sm text-slate-400">Redirecting to backtests...</p>
    </div>
  );
}
