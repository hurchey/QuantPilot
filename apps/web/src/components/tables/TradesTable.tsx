// apps/web/src/components/tables/TradesTable.tsx
import React from "react";

type Trade = {
  id?: number;
  symbol?: string;
  side?: string;
  qty?: number | string;
  quantity?: number | string;
  entry_price?: number | string;
  exit_price?: number | string;
  price?: number | string;
  pnl?: number | string;
  pnl_amount?: number | string;
  opened_at?: string;
  closed_at?: string;
  entry_time?: string;
  exit_time?: string;
  [key: string]: unknown;
};

type TradesTableProps = {
  trades: Trade[];
  className?: string;
  maxRows?: number;
};

function fmtNum(value: unknown, digits = 2): string {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "-";
}

function fmtDate(value: unknown): string {
  if (!value || typeof value !== "string") return "-";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

export default function TradesTable({
  trades,
  className = "",
  maxRows = 100,
}: TradesTableProps) {
  if (!trades?.length) {
    return <div className={`text-sm text-slate-400 ${className}`}>No trades found.</div>;
  }

  const rows = trades.slice(0, maxRows);

  return (
    <div className={`overflow-auto ${className}`}>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Entry</th>
            <th>Exit</th>
            <th>PnL</th>
            <th>Opened</th>
            <th>Closed</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((trade, idx) => {
            const qty = trade.qty ?? trade.quantity;
            const entry = trade.entry_price ?? trade.price;
            const exit = trade.exit_price;
            const pnl = trade.pnl ?? trade.pnl_amount;
            const side = String(trade.side ?? "-").toUpperCase();

            return (
              <tr key={trade.id ?? idx}>
                <td className="font-medium">{trade.symbol ?? "-"}</td>
                <td>
                  <span
                    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${
                      side === "BUY" || side === "LONG"
                        ? "border-emerald-700 text-emerald-300"
                        : side === "SELL" || side === "SHORT"
                        ? "border-red-700 text-red-300"
                        : "border-slate-700 text-slate-300"
                    }`}
                  >
                    {side}
                  </span>
                </td>
                <td>{fmtNum(qty, 4)}</td>
                <td>{fmtNum(entry, 4)}</td>
                <td>{fmtNum(exit, 4)}</td>
                <td
                  className={
                    Number(pnl) > 0
                      ? "text-emerald-300"
                      : Number(pnl) < 0
                      ? "text-red-300"
                      : ""
                  }
                >
                  {fmtNum(pnl, 2)}
                </td>
                <td>{fmtDate(trade.opened_at ?? trade.entry_time)}</td>
                <td>{fmtDate(trade.closed_at ?? trade.exit_time)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}