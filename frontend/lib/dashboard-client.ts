// Lightweight client-side fetcher with absolute URL handling (works in
// both server and client components). All endpoints live under /api/dashboard.

import type {
  AlertEvent,
  AttentionUnit,
  KPI,
  PipelineHealth,
  RegionPressure,
  TimeSeriesPoint,
  TopicSlice,
} from "./types";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return (await res.json()) as T;
}

export async function fetchKpis(): Promise<KPI[]> {
  const data = await getJson<{ items: KPI[] }>("/api/dashboard/kpis");
  return data.items;
}

export async function fetchHeatmap(): Promise<RegionPressure[]> {
  const data = await getJson<{ items: RegionPressure[] }>("/api/dashboard/heatmap");
  return data.items;
}

export async function fetchAttentionUnits(): Promise<AttentionUnit[]> {
  const data = await getJson<{ items: AttentionUnit[] }>(
    "/api/dashboard/units/attention",
  );
  return data.items;
}

export async function fetchTimeSeries(hours = 24): Promise<TimeSeriesPoint[]> {
  const data = await getJson<{ items: TimeSeriesPoint[] }>(
    `/api/dashboard/timeseries?hours=${hours}`,
  );
  return data.items;
}

export async function fetchTopics(): Promise<TopicSlice[]> {
  const data = await getJson<{ items: TopicSlice[] }>("/api/dashboard/topics");
  return data.items;
}

export async function fetchAlerts(): Promise<AlertEvent[]> {
  const data = await getJson<{ items: AlertEvent[] }>("/api/dashboard/alerts");
  return data.items;
}

export async function fetchPipelineHealth(): Promise<PipelineHealth> {
  return getJson<PipelineHealth>("/api/dashboard/health");
}
