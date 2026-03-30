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
    <section
      className={`border border-neutral-800 bg-neutral-950 relative ${className}`}
    >
      {/* Top glow line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neutral-700 to-transparent" />

      {(title || subtitle || actions) && (
        <div className="flex flex-wrap items-start justify-between gap-3 border-b border-neutral-800 px-4 py-3">
          <div>
            {title ? (
              <h2 className="text-xs font-semibold tracking-[0.12em] uppercase text-neutral-400">
                {title}
              </h2>
            ) : null}
            {subtitle ? (
              <p className="text-[0.7rem] text-neutral-600 mt-0.5">{subtitle}</p>
            ) : null}
          </div>
          {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
        </div>
      )}

      <div className="p-4">{children}</div>
    </section>
  );
}
