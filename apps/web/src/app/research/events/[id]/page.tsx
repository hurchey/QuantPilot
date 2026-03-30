"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import ErrorBanner from "@/components/ui/ErrorBanner";
import { formatNumber, formatPercent, formatShortDate } from "@/lib/format";

type DislocationEvent = {
  id: number;
  symbol: string;
  company_name: string | null;
  security_type: string | null;
  event_start_date: string;
  event_end_date: string;
  peak_date: string | null;
  price_start: number;
  price_peak: number;
  price_end_3d: number | null;
  return_1d_pct: number | null;
  return_3d_pct: number;
  return_peak_pct: number | null;
  label_a: number;
  label_b: number;
  day_after_continuation: number | null;
  volume_event_day: number | null;
  volume_avg_20d_pre: number | null;
  volume_ratio: number | null;
  shares_outstanding: number | null;
  float_shares: number | null;
  market_cap_pre: number | null;
  short_interest_shares: number | null;
  short_pct_float: number | null;
  days_to_cover: number | null;
  sector: string | null;
  industry: string | null;
  exchange: string | null;
  ipo_date: string | null;
  days_since_ipo: number | null;
  catalyst_summary: string | null;
  options_available: number | null;
  iv_pre_event: number | null;
  taxonomy_bucket: string | null;
  taxonomy_confidence: number | null;
  taxonomy_notes: string | null;
  data_source: string | null;
  created_at: string | null;
};

type DislocationFeature = {
  id: number;
  event_id: number;
  feature_name: string;
  feature_value: string | null;
  feature_numeric: number | null;
  feature_json: unknown;
};

type EventDetail = {
  event: DislocationEvent;
  features: DislocationFeature[];
};

function DataRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between py-1.5 border-b border-neutral-900">
      <span className="text-[0.65rem] uppercase tracking-[0.1em] text-neutral-600">
        {label}
      </span>
      <span
        className={`text-sm font-mono ${highlight ? "text-white font-bold" : "text-neutral-400"}`}
      >
        {value ?? "--"}
      </span>
    </div>
  );
}

export default function EventDetailPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params?.id as string;

  const [data, setData] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) return;

    async function load() {
      setLoading(true);
      try {
        const res = await apiGet<EventDetail>(
          `/quant/research/events/${eventId}`
        );
        setData(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load event");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [eventId]);

  if (loading) {
    return (
      <div className="py-16 flex justify-center">
        <LoadingSpinner text="LOADING EVENT..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 py-8">
        <ErrorBanner message={error} />
        <button
          onClick={() => router.back()}
          className="text-[0.7rem] uppercase tracking-wider text-neutral-500 hover:text-white transition-colors"
        >
          &larr; Back
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { event: ev, features } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            href="/research"
            className="text-[0.6rem] uppercase tracking-[0.15em] text-neutral-600 hover:text-white transition-colors"
          >
            &larr; Research Hub
          </Link>
          <div className="mt-2 flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-wider text-white">
              {ev.symbol}
            </h1>
            {ev.label_b === 1 && (
              <span className="border border-neutral-600 px-2 py-0.5 text-[0.55rem] uppercase tracking-wider text-neutral-400">
                1000%+ Dislocation
              </span>
            )}
            {ev.label_a === 1 && ev.label_b !== 1 && (
              <span className="border border-neutral-700 px-2 py-0.5 text-[0.55rem] uppercase tracking-wider text-neutral-500">
                500%+ Dislocation
              </span>
            )}
            {ev.taxonomy_bucket && (
              <span className="qp-badge">{ev.taxonomy_bucket}</span>
            )}
          </div>
          {ev.company_name && (
            <p className="text-[0.75rem] text-neutral-500 mt-1">
              {ev.company_name}
            </p>
          )}
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-white tracking-wide">
            {formatPercent(ev.return_3d_pct)}
          </div>
          <div className="text-[0.6rem] uppercase tracking-[0.15em] text-neutral-600 mt-1">
            3-Day Return
          </div>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Price data */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Price Action
          </h2>
          <DataRow label="Start Price" value={`$${formatNumber(ev.price_start, { maximumFractionDigits: 4 })}`} />
          <DataRow label="Peak Price" value={`$${formatNumber(ev.price_peak, { maximumFractionDigits: 4 })}`} highlight />
          <DataRow label="3d End Price" value={ev.price_end_3d != null ? `$${formatNumber(ev.price_end_3d, { maximumFractionDigits: 4 })}` : null} />
          <DataRow label="1d Return" value={ev.return_1d_pct != null ? formatPercent(ev.return_1d_pct) : null} />
          <DataRow label="3d Return" value={formatPercent(ev.return_3d_pct)} highlight />
          <DataRow label="Peak Return" value={ev.return_peak_pct != null ? formatPercent(ev.return_peak_pct) : null} />
          <DataRow
            label="Continuation"
            value={
              ev.day_after_continuation === 1
                ? "YES"
                : ev.day_after_continuation === 0
                  ? "NO"
                  : null
            }
            highlight={ev.day_after_continuation === 1}
          />
        </div>

        {/* Volume & structure */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Volume & Structure
          </h2>
          <DataRow
            label="Event Day Volume"
            value={
              ev.volume_event_day != null
                ? formatNumber(ev.volume_event_day, { maximumFractionDigits: 0 })
                : null
            }
          />
          <DataRow
            label="Avg 20d Volume"
            value={
              ev.volume_avg_20d_pre != null
                ? formatNumber(ev.volume_avg_20d_pre, { maximumFractionDigits: 0 })
                : null
            }
          />
          <DataRow
            label="Volume Ratio"
            value={
              ev.volume_ratio != null
                ? `${formatNumber(ev.volume_ratio, { maximumFractionDigits: 1 })}x`
                : null
            }
            highlight={ev.volume_ratio != null && ev.volume_ratio > 10}
          />
          <DataRow
            label="Shares Outstanding"
            value={
              ev.shares_outstanding != null
                ? formatNumber(ev.shares_outstanding, { maximumFractionDigits: 0 })
                : null
            }
          />
          <DataRow
            label="Float"
            value={
              ev.float_shares != null
                ? formatNumber(ev.float_shares, { maximumFractionDigits: 0 })
                : null
            }
          />
          <DataRow
            label="Market Cap (Pre)"
            value={
              ev.market_cap_pre != null
                ? `$${formatNumber(ev.market_cap_pre, { maximumFractionDigits: 0 })}`
                : null
            }
          />
        </div>

        {/* Short interest & fundamentals */}
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Short Interest & Info
          </h2>
          <DataRow
            label="Short Interest"
            value={
              ev.short_interest_shares != null
                ? formatNumber(ev.short_interest_shares, { maximumFractionDigits: 0 })
                : null
            }
          />
          <DataRow
            label="Short % Float"
            value={ev.short_pct_float != null ? formatPercent(ev.short_pct_float) : null}
            highlight={ev.short_pct_float != null && ev.short_pct_float > 20}
          />
          <DataRow
            label="Days to Cover"
            value={ev.days_to_cover != null ? formatNumber(ev.days_to_cover, { maximumFractionDigits: 1 }) : null}
          />
          <DataRow label="Sector" value={ev.sector} />
          <DataRow label="Industry" value={ev.industry} />
          <DataRow label="Exchange" value={ev.exchange} />
          <DataRow label="IPO Date" value={ev.ipo_date ? formatShortDate(ev.ipo_date) : null} />
          <DataRow
            label="Days Since IPO"
            value={ev.days_since_ipo != null ? formatNumber(ev.days_since_ipo, { maximumFractionDigits: 0 }) : null}
          />
        </div>
      </div>

      {/* Timeline & dates */}
      <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
        <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
          Event Timeline
        </h2>
        <div className="flex items-center gap-8 flex-wrap text-sm">
          <div>
            <div className="text-[0.6rem] uppercase tracking-wider text-neutral-600">Start</div>
            <div className="text-white font-mono">{ev.event_start_date?.split("T")[0]}</div>
          </div>
          <div className="text-neutral-700">&rarr;</div>
          {ev.peak_date && (
            <>
              <div>
                <div className="text-[0.6rem] uppercase tracking-wider text-neutral-600">Peak</div>
                <div className="text-white font-mono">{ev.peak_date.split("T")[0]}</div>
              </div>
              <div className="text-neutral-700">&rarr;</div>
            </>
          )}
          <div>
            <div className="text-[0.6rem] uppercase tracking-wider text-neutral-600">End (3d)</div>
            <div className="text-neutral-400 font-mono">{ev.event_end_date?.split("T")[0]}</div>
          </div>
        </div>
      </div>

      {/* Taxonomy & catalyst */}
      {(ev.taxonomy_bucket || ev.catalyst_summary) && (
        <div className="border border-neutral-800 bg-neutral-950 p-4 relative">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500 mb-3">
            Classification
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {ev.taxonomy_bucket && (
              <div>
                <DataRow label="Bucket" value={ev.taxonomy_bucket} highlight />
                <DataRow
                  label="Confidence"
                  value={ev.taxonomy_confidence != null ? formatPercent(ev.taxonomy_confidence * 100) : null}
                />
                {ev.taxonomy_notes && (
                  <div className="mt-2 text-[0.75rem] text-neutral-500">
                    {ev.taxonomy_notes}
                  </div>
                )}
              </div>
            )}
            {ev.catalyst_summary && (
              <div>
                <div className="text-[0.6rem] uppercase tracking-[0.1em] text-neutral-600 mb-1">
                  Catalyst
                </div>
                <p className="text-sm text-neutral-300">{ev.catalyst_summary}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Features table */}
      {features.length > 0 && (
        <div className="border border-neutral-800 bg-neutral-950 relative overflow-x-auto">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />
          <div className="px-4 py-3 border-b border-neutral-800">
            <h2 className="text-[0.65rem] font-semibold uppercase tracking-[0.15em] text-neutral-500">
              Features ({features.length})
            </h2>
          </div>
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Value</th>
                <th>Numeric</th>
              </tr>
            </thead>
            <tbody>
              {features.map((f) => (
                <tr key={f.id}>
                  <td className="text-neutral-300 font-mono text-[0.75rem]">
                    {f.feature_name}
                  </td>
                  <td className="text-neutral-500">{f.feature_value ?? "--"}</td>
                  <td className="text-neutral-400 font-mono">
                    {f.feature_numeric != null
                      ? formatNumber(f.feature_numeric)
                      : "--"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Meta */}
      <div className="text-[0.6rem] text-neutral-700 flex items-center gap-4">
        <span>ID: {ev.id}</span>
        {ev.data_source && <span>Source: {ev.data_source}</span>}
        {ev.created_at && <span>Created: {ev.created_at.split("T")[0]}</span>}
        {ev.options_available != null && (
          <span>Options: {ev.options_available ? "Yes" : "No"}</span>
        )}
      </div>
    </div>
  );
}
