"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

type Mode = "register" | "login";

export default function LoginPage() {
  const router = useRouter();

  const [mode, setMode] = useState<Mode>("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("My Workspace");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (mode === "register") {
        await apiFetch("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            email,
            password,
            workspace_name: workspaceName,
          }),
        });
      } else {
        await apiFetch("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
      }

      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container" style={{ maxWidth: 520 }}>
      <div className="card" style={{ padding: 24 }}>
        <h1 className="title">WorkPilot</h1>
        <p className="subtitle">
          {mode === "register" ? "Create your account" : "Sign in to your workspace"}
        </p>

        <form onSubmit={onSubmit} className="grid" style={{ marginTop: 16 }}>
          <input
            className="input"
            type="email"
            placeholder="Email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            className="input"
            type="password"
            placeholder="Password (min 8 chars)"
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {mode === "register" && (
            <input
              className="input"
              placeholder="Workspace name"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              required
            />
          )}

          {error ? (
            <div
              className="card"
              style={{ borderColor: "#fecaca", background: "#fef2f2", color: "#991b1b" }}
            >
              {error}
            </div>
          ) : null}

          <button className="button" type="submit" disabled={loading}>
            {loading
              ? "Please wait..."
              : mode === "register"
              ? "Create account"
              : "Log in"}
          </button>
        </form>

        <div className="row" style={{ marginTop: 12 }}>
          <span className="muted" style={{ fontSize: 14 }}>
            {mode === "register" ? "Already have an account?" : "Need an account?"}
          </span>
          <button
            type="button"
            className="button secondary"
            onClick={() => {
              setMode(mode === "register" ? "login" : "register");
              setError("");
            }}
          >
            Switch to {mode === "register" ? "Login" : "Register"}
          </button>
        </div>
      </div>
    </main>
  );
}