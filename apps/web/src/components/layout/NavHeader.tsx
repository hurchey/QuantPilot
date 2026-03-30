"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

const NAV_LINKS = [
  { href: "/research", label: "RESEARCH" },
  { href: "/research/universe", label: "UNIVERSE" },
] as const;

export default function NavHeader() {
  const { isAuthenticated, logout, user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  function handleLogout() {
    logout();
    router.push("/");
  }

  return (
    <header className="border-b border-neutral-800 bg-black/95 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
        <Link
          href="/"
          className="font-bold text-sm tracking-[0.2em] text-white uppercase hover:opacity-80 transition-opacity"
        >
          QUANTPILOT
        </Link>

        <nav className="flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => {
            const isActive = pathname === href || pathname?.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={cx(
                  "px-2.5 py-1.5 text-[0.65rem] font-semibold tracking-[0.1em] uppercase transition-all",
                  isActive
                    ? "text-white border-b border-white"
                    : "text-neutral-500 hover:text-white"
                )}
              >
                {label}
              </Link>
            );
          })}

          <span className="mx-2 h-3 w-px bg-neutral-800" />

          {loading ? (
            <span className="text-neutral-600 text-[0.65rem]">...</span>
          ) : isAuthenticated ? (
            <>
              <Link
                href="/research"
                className="px-2 py-1 text-[0.65rem] font-semibold tracking-[0.1em] uppercase text-neutral-500 hover:text-white transition-colors"
                title={user?.email || user?.name || "Account"}
              >
                ACCT
              </Link>
              <button
                onClick={handleLogout}
                className="px-2 py-1 text-[0.65rem] font-semibold tracking-[0.1em] uppercase text-neutral-600 hover:text-red-400 transition-colors"
              >
                EXIT
              </button>
            </>
          ) : (
            <>
              <Link
                href="/auth/login"
                className="px-2 py-1 text-[0.65rem] font-semibold tracking-[0.1em] uppercase text-neutral-500 hover:text-white transition-colors"
              >
                LOGIN
              </Link>
              <Link
                href="/auth/register"
                className="px-2 py-1 text-[0.65rem] font-semibold tracking-[0.1em] uppercase bg-white text-black transition-colors hover:bg-neutral-200"
              >
                REGISTER
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
