// apps/web/src/app/layout.tsx
import type { Metadata } from "next";
import "./global.css";
import NavHeader from "@/components/layout/NavHeader";

export const metadata: Metadata = {
  title: "QuantPilot",
  description: "Quant-focused full-stack SaaS project",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <div className="min-h-screen">
          <NavHeader />

          <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}