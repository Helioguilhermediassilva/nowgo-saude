// Server-side client for the FastAPI backend (Feature 001).
// Only runs in Server Components / Route Handlers — never in the browser —
// because admin-protected endpoints require a bearer token that must stay
// out of the client bundle. All helpers return `null` on failure so callers
// can transparently fall back to the mock layer.

import "server-only";

import type { MetricsSummary, PipelineHealthBackend } from "./types";

type FetchOpts = {
  path: string;
  auth?: boolean;
  // Backend metrics rarely change faster than 30s; mirror /health cadence.
  revalidate?: number;
};

function backendBaseUrl(): string | null {
  const url = process.env.BACKEND_API_URL?.replace(/\/+$/, "");
  return url && url.length > 0 ? url : null;
}

async function backendFetch<T>({ path, auth = false, revalidate = 15 }: FetchOpts): Promise<T | null> {
  const base = backendBaseUrl();
  if (!base) return null;

  const headers: Record<string, string> = { Accept: "application/json" };
  if (auth) {
    const token = process.env.BACKEND_API_TOKEN;
    if (!token) return null;
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${base}${path}`, {
      headers,
      next: { revalidate },
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export async function getBackendHealth(): Promise<PipelineHealthBackend | null> {
  return backendFetch<PipelineHealthBackend>({ path: "/health", auth: false, revalidate: 10 });
}

export async function getBackendMetrics(): Promise<MetricsSummary | null> {
  return backendFetch<MetricsSummary>({ path: "/api/v1/metrics", auth: true, revalidate: 30 });
}

export function isBackendConfigured(): boolean {
  return backendBaseUrl() !== null;
}
