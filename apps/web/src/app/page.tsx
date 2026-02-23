import Link from "next/link";

export default function HomePage() {
  return (
    <main className="container">
      <div className="card" style={{ padding: 24 }}>
        <h1 className="title">WorkPilot</h1>
        <p className="subtitle">
          A resume-optimized SaaS MVP for task workflows (Next.js + FastAPI + Supabase Postgres)
        </p>

        <div style={{ marginTop: 16 }} className="row">
          <Link href="/login" className="button">
            Get Started
          </Link>
          <a
            className="button secondary"
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            API Docs
          </a>
        </div>
      </div>
    </main>
  );
}