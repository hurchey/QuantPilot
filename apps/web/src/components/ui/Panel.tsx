// apps/web/src/components/ui/Panel.tsx
import * as React from "react";

type PanelProps = {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
};

export function Panel({
  title,
  subtitle,
  actions,
  children,
  className = "",
}: PanelProps) {
  return (
    <section className={`rounded-2xl border border-slate-800 bg-slate-900 ${className}`}>
      {(title || subtitle || actions) && (
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-800 px-4 py-3">
          <div>
            {title ? <h2 className="text-lg font-semibold">{title}</h2> : null}
            {subtitle ? (
              <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>
            ) : null}
          </div>
          {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
        </div>
      )}

      <div className="p-4">{children}</div>
    </section>
  );
}