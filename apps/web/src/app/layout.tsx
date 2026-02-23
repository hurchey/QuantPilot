import "./global.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "WorkPilot",
  description: "Resume-optimized full-stack SaaS MVP",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}