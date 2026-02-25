"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  apiFetch,
  clearAuthToken,
  getAuthToken,
  setAuthToken,
} from "@/lib/api";

export type AuthUser = {
  id?: number | string;
  email?: string;
  username?: string;
  full_name?: string;
  name?: string;
};

type LoginInput = {
  email: string;
  password: string;
};

type RegisterInput = {
  email: string;
  password: string;
  name?: string;
};

type AuthResponse = {
  access_token?: string;
  token?: string;
  token_type?: string;
  user?: AuthUser;
  [key: string]: unknown;
};

const USER_STORAGE_KEY = "qp_auth_user";

function readStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

function writeStoredUser(user: AuthUser | null) {
  if (typeof window === "undefined") return;
  if (!user) {
    localStorage.removeItem(USER_STORAGE_KEY);
    return;
  }
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

function normalizeUser(payload: unknown): AuthUser | null {
  if (!payload || typeof payload !== "object") return null;
  const p = payload as Record<string, unknown>;

  return {
    id: (p.id as number | string) ?? undefined,
    email: typeof p.email === "string" ? p.email : undefined,
    username: typeof p.username === "string" ? p.username : undefined,
    full_name: typeof p.full_name === "string" ? p.full_name : undefined,
    name:
      typeof p.name === "string"
        ? p.name
        : typeof p.full_name === "string"
        ? p.full_name
        : undefined,
  };
}

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true); // initial auth bootstrap
  const [authLoading, setAuthLoading] = useState(false); // login/register action
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = useMemo(() => !!getAuthToken(), [user]);

  const hydrateUser = useCallback(async () => {
    const token = getAuthToken();

    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    // Start with cached user to avoid flicker
    const cached = readStoredUser();
    if (cached) setUser(cached);

    // Try common "me" endpoints, but don't fail hard if not implemented
    try {
      const me = await apiFetch<unknown>("/auth/me");
      const parsed = normalizeUser(me);
      if (parsed) {
        setUser(parsed);
        writeStoredUser(parsed);
      }
    } catch {
      try {
        const meAlt = await apiFetch<unknown>("/users/me");
        const parsedAlt = normalizeUser(meAlt);
        if (parsedAlt) {
          setUser(parsedAlt);
          writeStoredUser(parsedAlt);
        }
      } catch {
        // It's okay if /me endpoint isn't implemented
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    hydrateUser();
  }, [hydrateUser]);

  const login = useCallback(async ({ email, password }: LoginInput) => {
    setAuthLoading(true);
    setError(null);

    try {
      let res: AuthResponse | null = null;

      // FastAPI OAuth2PasswordRequestForm usually expects x-www-form-urlencoded
      const form = new URLSearchParams();
      form.set("username", email); // backend commonly uses username field
      form.set("password", password);

      try {
        res = await apiFetch<AuthResponse>("/auth/login", {
          method: "POST",
          body: form,
          skipAuth: true,
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        });
      } catch {
        // Fallbacks for different backend route/payload shapes
        try {
          res = await apiFetch<AuthResponse>("/login", {
            method: "POST",
            body: form,
            skipAuth: true,
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
          });
        } catch {
          res = await apiFetch<AuthResponse>("/auth/login", {
            method: "POST",
            body: JSON.stringify({ email, username: email, password }),
            skipAuth: true,
          });
        }
      }

      const token = res?.access_token || res?.token;
      if (!token) {
        throw new Error("Login succeeded but no access token was returned.");
      }

      setAuthToken(token);

      const maybeUser = normalizeUser(res?.user);
      if (maybeUser) {
        setUser(maybeUser);
        writeStoredUser(maybeUser);
      } else {
        // Try to fetch /me if available
        try {
          const me = await apiFetch<unknown>("/auth/me");
          const parsed = normalizeUser(me);
          if (parsed) {
            setUser(parsed);
            writeStoredUser(parsed);
          } else {
            // fallback lightweight local user
            const fallbackUser: AuthUser = { email, username: email };
            setUser(fallbackUser);
            writeStoredUser(fallbackUser);
          }
        } catch {
          const fallbackUser: AuthUser = { email, username: email };
          setUser(fallbackUser);
          writeStoredUser(fallbackUser);
        }
      }

      return true;
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Login failed.";
      setError(msg);
      return false;
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const register = useCallback(
    async ({ email, password, name }: RegisterInput) => {
      setAuthLoading(true);
      setError(null);

      try {
        const username = email.includes("@") ? email.split("@")[0] : email;

        const payload = {
          email,
          password,
          username, // many FastAPI examples include username
          full_name: name || undefined,
          name: name || undefined,
        };

        let res: AuthResponse | null = null;

        try {
          res = await apiFetch<AuthResponse>("/auth/register", {
            method: "POST",
            body: JSON.stringify(payload),
            skipAuth: true,
          });
        } catch {
          res = await apiFetch<AuthResponse>("/register", {
            method: "POST",
            body: JSON.stringify(payload),
            skipAuth: true,
          });
        }

        // Some backends return token on register, some don't.
        const token = res?.access_token || res?.token;
        if (token) {
          setAuthToken(token);
          const maybeUser = normalizeUser(res?.user) || {
            email,
            username,
            name,
            full_name: name,
          };
          setUser(maybeUser);
          writeStoredUser(maybeUser);
          return true;
        }

        // If no token returned, immediately log in
        setAuthLoading(false);
        return await login({ email, password });
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Registration failed.";
        setError(msg);
        return false;
      } finally {
        setAuthLoading(false);
      }
    },
    [login]
  );

  const logout = useCallback(() => {
    clearAuthToken();
    writeStoredUser(null);
    setUser(null);
    setError(null);
  }, []);

  const refreshUser = useCallback(async () => {
    setLoading(true);
    await hydrateUser();
  }, [hydrateUser]);

  return {
    user,
    loading,
    authLoading,
    error,
    setError,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
  };
}