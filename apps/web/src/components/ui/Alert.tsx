// apps/web/src/components/ui/Alert.tsx
import * as React from "react";

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

type AlertProps = {
  variant?: "info" | "success" | "error" | "warning";
  title?: string;
  children: React.ReactNode;
  className?: string;
};

export function Alert({
  variant = "info",
  title,
  children,
  className,
}: AlertProps) {
  const variants = {
    info: "border-blue-900 bg-blue-950/30 text-blue-200",
    success: "border-emerald-900 bg-emerald-950/30 text-emerald-200",
    error: "border-red-900 bg-red-950/30 text-red-200",
    warning: "border-amber-900 bg-amber-950/30 text-amber-200",
  } as const;

  return (
    <div className={cx("rounded-xl border p-3", variants[variant], className)}>
      {title ? <div className="font-semibold mb-1">{title}</div> : null}
      <div className="text-sm">{children}</div>
    </div>
  );
}