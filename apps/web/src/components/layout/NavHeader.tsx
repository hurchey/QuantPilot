"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function NavHeader() {
  const { isAuthenticated, logout, user, loading } = useAuth();
  const router = useRouter();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
      <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
        <Link href="/" className="font-semibold text-lg">
          QuantPilot
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="hover:text-white text-slate-300">
            Dashboard
          </Link>
          <Link href="/workflow" className="hover:text-white text-slate-300">
            Workflow
          </Link>
          <Link href="/strategies" className="hover:text-white text-slate-300">
            Strategies
          </Link>
          <Link href="/data" className="hover:text-white text-slate-300">
            Market Data
          </Link>
          <Link href="/backtests" className="hover:text-white text-slate-300">
            Backtests
          </Link>
          <Link href="/backtest-pipeline" className="hover:text-white text-slate-300">
            Pipeline
          </Link>
          <Link href="/stocks" className="hover:text-white text-slate-300">
            Stock Profile
          </Link>

          {loading ? (
            <span className="text-slate-500">...</span>
          ) : isAuthenticated ? (
            <>
              <Link
                href="/dashboard"
                className="hover:text-white text-slate-300"
                title={user?.email || user?.name || "Account"}
              >
                Account
              </Link>
              <button
                onClick={handleLogout}
                className="hover:text-white text-slate-300"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/auth/login" className="hover:text-white text-slate-300">
                Login
              </Link>
              <Link href="/auth/register" className="hover:text-white text-slate-300">
                Register
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
