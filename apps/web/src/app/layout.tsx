// apps/web/src/app/layout.tsx
import type { Metadata } from "next";
import Link from "next/link";
import "./global.css";

export const metadata: Metadata = {
  title: "QuantPilot",
  description: "Quant-focused full-stack SaaS project",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <div className="min-h-screen">
          <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
            <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
              <Link href="/" className="font-semibold text-lg">
                QuantPilot
              </Link>
              <nav className="flex items-center gap-4 text-sm">
                <Link href="/dashboard" className="hover:text-white text-slate-300">Dashboard</Link>
                <Link href="/strategies" className="hover:text-white text-slate-300">Strategies</Link>
                <Link href="/data" className="hover:text-white text-slate-300">Market Data</Link>
                <Link href="/backtests" className="hover:text-white text-slate-300">Backtests</Link>
                <Link href="/auth/login" className="hover:text-white text-slate-300">Login</Link>
                <Link href="/auth/register" className="hover:text-white text-slate-300">Register</Link>
              </nav>
            </div>
          </header>

          <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}