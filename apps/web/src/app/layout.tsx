// apps/web/src/app/layout.tsx
import type { Metadata } from "next";
import "./global.css";
import NavHeader from "@/components/layout/NavHeader";

export const metadata: Metadata = {
  title: "QuantPilot",
  description: "Quantitative research into extreme price dislocations",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="bg-black text-neutral-300 min-h-screen">
        <div className="min-h-screen">
          <NavHeader />

          <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
