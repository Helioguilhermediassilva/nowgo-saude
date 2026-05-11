// Server-side client for the FastAPI backend (Feature 001).
// Only runs in Server Components / Route Handlers — never in the browser —
// because admin-protected endpoints require a bearer token that must stay
// out of the client bundle. All helpers return `null` on failure so callers
// can transparently fall back to the mock layer.

import "server-only";

import type {
  AlertEvent,
  AttentionUnit,
  KPI,
  MetricsSummary,
  PipelineHealth,
  PipelineHealthBackend,
  RegionPressure,
  TimeSeriesPoint,
  TopicSlice,
} from "./types";

interface ItemsEnvelope<T> {
  items: T[];
}

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

// Feature 002 — Command Center Dashboard aggregations.
// All endpoints require the admin bearer; payloads use camelCase keys
// matching the frontend types in `./types`.

export async function getBackendDashboardHealth(): Promise<PipelineHealth | null> {
  return backendFetch<PipelineHealth>({
    path: "/api/v1/dashboard/health",
    auth: true,
    revalidate: 15,
  });
}

export async function getBackendDashboardKpis(): Promise<KPI[] | null> {
  const env = await backendFetch<ItemsEnvelope<KPI>>({
    path: "/api/v1/dashboard/kpis",
    auth: true,
    revalidate: 30,
  });
  return env?.items ?? null;
}

export async function getBackendDashboardHeatmap(): Promise<RegionPressure[] | null> {
  const env = await backendFetch<ItemsEnvelope<RegionPressure>>({
    path: "/api/v1/dashboard/heatmap",
    auth: true,
    revalidate: 30,
  });
  return env?.items ?? null;
}

export async function getBackendDashboardAttention(limit = 12): Promise<AttentionUnit[] | null> {
  const env = await backendFetch<ItemsEnvelope<AttentionUnit>>({
    path: `/api/v1/dashboard/units/attention?limit=${limit}`,
    auth: true,
    revalidate: 30,
  });
  return env?.items ?? null;
}

export async function getBackendDashboardTopics(): Promise<TopicSlice[] | null> {
  const env = await backendFetch<ItemsEnvelope<TopicSlice>>({
    path: "/api/v1/dashboard/topics",
    auth: true,
    revalidate: 60,
  });
  return env?.items ?? null;
}

export async function getBackendDashboardTimeseries(hours = 24): Promise<TimeSeriesPoint[] | null> {
  const env = await backendFetch<ItemsEnvelope<TimeSeriesPoint>>({
    path: `/api/v1/dashboard/timeseries?hours=${hours}`,
    auth: true,
    revalidate: 30,
  });
  return env?.items ?? null;
}

export async function getBackendDashboardAlerts(limit = 12): Promise<AlertEvent[] | null> {
  const env = await backendFetch<ItemsEnvelope<AlertEvent>>({
    path: `/api/v1/dashboard/alerts?limit=${limit}`,
    auth: true,
    revalidate: 15,
  });
  return env?.items ?? null;
}

export function isBackendConfigured(): boolean {
  return backendBaseUrl() !== null;
}
