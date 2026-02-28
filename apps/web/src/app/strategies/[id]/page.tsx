"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";

/**
 * Redirect /strategies/[id] to /strategies.
 * Strategy management is on the main strategies page.
 */
export default function StrategyDetailPage() {
  const router = useRouter();
  const params = useParams();

  useEffect(() => {
    router.replace("/strategies");
  }, [router, params]);

  return (
    <div className="flex min-h-[200px] items-center justify-center">
      <p className="text-sm text-slate-400">Redirecting to strategies...</p>
    </div>
  );
}
