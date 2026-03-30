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
    size === "sm" ? "h-3 w-3" : size === "lg" ? "h-6 w-6" : "h-4 w-4";

  const wrapperClass = center
    ? "flex items-center justify-center"
    : "flex items-center";

  return (
    <div className={`${wrapperClass} gap-3 text-neutral-500 ${className}`}>
      <span
        aria-hidden="true"
        className={`${spinnerSize} inline-block animate-spin border border-neutral-700 border-t-white`}
      />
      {text ? (
        <span className="text-[0.7rem] uppercase tracking-[0.1em]">{text}</span>
      ) : null}
    </div>
  );
}
