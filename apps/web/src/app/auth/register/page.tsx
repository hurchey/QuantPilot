"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const router = useRouter();
  const { register, authLoading, error, setError, isAuthenticated, loading } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [loading, isAuthenticated, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    const ok = await register({ name, email, password });
    if (ok) {
      router.replace("/dashboard");
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl">
        <div className="mb-5">
          <h1 className="text-2xl font-semibold tracking-tight">Create account</h1>
          <p className="mt-1 text-sm text-slate-400">
            Sign up to save strategies, upload market data, and run backtests.
          </p>
        </div>

        {error ? (
          <div className="mb-4 rounded-lg border border-red-900/50 bg-red-950/40 px-3 py-2 text-sm text-red-200">
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-300">
              Name
            </label>
            <input
              type="text"
              autoComplete="name"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none placeholder:text-slate-500 focus:border-slate-500"
              placeholder="Eric Hurchey"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-300">
              Email
            </label>
            <input
              type="email"
              autoComplete="email"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none placeholder:text-slate-500 focus:border-slate-500"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-300">
              Password
            </label>
            <input
              type="password"
              autoComplete="new-password"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none placeholder:text-slate-500 focus:border-slate-500"
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              maxLength={72}
            />
            <p className="mt-1 text-xs text-slate-500">
              Max 72 characters to avoid bcrypt length issues.
            </p>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-slate-300">
              Confirm password
            </label>
            <input
              type="password"
              autoComplete="new-password"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none placeholder:text-slate-500 focus:border-slate-500"
              placeholder="Re-enter password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              maxLength={72}
            />
          </div>

          <button
            type="submit"
            disabled={authLoading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {authLoading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <div className="mt-4 text-sm text-slate-400">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-blue-400 hover:text-blue-300">
            Log in
          </Link>
        </div>
      </div>
    </div>
  );
}