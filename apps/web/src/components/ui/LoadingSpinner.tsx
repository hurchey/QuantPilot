import React from "react";

type LoadingSpinnerProps = {
  text?: string;
  size?: "sm" | "md" | "lg";
  center?: boolean;
  className?: string;
};

export default function LoadingSpinner({
  text,
  size = "md",
  center = false,
  className = "",
}: LoadingSpinnerProps) {
  const spinnerSize =
    size === "sm" ? "h-4 w-4" : size === "lg" ? "h-8 w-8" : "h-6 w-6";

  const wrapperClass = center
    ? "flex items-center justify-center"
    : "flex items-center";

  return (
    <div className={`${wrapperClass} gap-2 text-slate-300 ${className}`}>
      <span
        aria-hidden="true"
        className={`${spinnerSize} inline-block animate-spin rounded-full border-2 border-slate-700 border-t-slate-200`}
      />
      {text ? <span className="text-sm">{text}</span> : null}
    </div>
  );
}