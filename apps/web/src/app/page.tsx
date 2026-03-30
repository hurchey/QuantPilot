// apps/web/src/app/page.tsx
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-8 py-8">
      <section className="border border-neutral-800 bg-neutral-950 p-8 relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
        <h1 className="text-lg font-bold tracking-[0.15em] uppercase text-white">
          QuantPilot
        </h1>
        <p className="text-[0.8rem] text-neutral-500 mt-2 max-w-xl leading-relaxed">
          Quantitative research into extreme price dislocations. Discover events,
          build filtered universes, classify by taxonomy, and analyze continuation patterns.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          href="/research"
          className="border border-neutral-800 bg-neutral-950 p-5 hover:border-neutral-600 transition-all group relative"
        >
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            Research Hub
          </div>
          <div className="text-sm text-neutral-300">
            Scan symbols, view dislocation events, filter by label and taxonomy bucket.
          </div>
        </Link>
        <Link
          href="/research/universe"
          className="border border-neutral-800 bg-neutral-950 p-5 hover:border-neutral-600 transition-all group relative"
        >
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            Universe Builder
          </div>
          <div className="text-sm text-neutral-300">
            Build and manage filtered stock universes for systematic scanning.
          </div>
        </Link>
        <Link
          href="/research"
          className="border border-neutral-800 bg-neutral-950 p-5 hover:border-neutral-600 transition-all group relative"
        >
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          <div className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-1">
            Export Data
          </div>
          <div className="text-sm text-neutral-300">
            Export filtered events as CSV or JSON for further analysis.
          </div>
        </Link>
      </section>
    </div>
  );
}