// Server-side data accessors used by the dashboard during SSR.
// When BACKEND_API_URL is configured, every accessor bridges to the FastAPI
// dashboard endpoints (Feature 002) and falls back to the mock layer if the
// backend is unreachable, unauthenticated, or returns no data. This keeps
// previews and offline development functional while production renders the
// real Postgres-backed aggregations.

import "server-only";

import {
  getBackendDashboardAlerts,
  getBackendDashboardAttention,
  getBackendDashboardHealth,
  getBackendDashboardHeatmap,
  getBackendDashboardKpis,
  getBackendDashboardRegion,
  getBackendDashboardTimeseries,
  getBackendDashboardTopics,
  getBackendDashboardUnit,
  getBackendHealth,
  getBackendMetrics,
  isBackendConfigured,
} from "./backend-client";
import {
  getAlerts as mockGetAlerts,
  getAttentionUnits as mockGetAttentionUnits,
  getHeatmap as mockGetHeatmap,
  getKpis as mockGetKpis,
  getPipelineHealth as mockGetPipelineHealth,
  getRegionDetail as mockGetRegionDetail,
  getTimeSeries as mockGetTimeSeries,
  getTopics as mockGetTopics,
  getUnitDetail as mockGetUnitDetail,
} from "./mock-data";
import type {
  AlertEvent,
  AttentionUnit,
  KPI,
  PipelineHealth,
  RegionDetail,
  RegionPressure,
  TimeSeriesPoint,
  TopicSlice,
  UnitDetail,
} from "./types";

const LATENCY_THRESHOLD_SECONDS = 300;

export async function getKpis(): Promise<KPI[]> {
  if (!isBackendConfigured()) return mockGetKpis();
  const live = await getBackendDashboardKpis();
  return live && live.length > 0 ? live : mockGetKpis();
}

export async function getHeatmap(): Promise<RegionPressure[]> {
  if (!isBackendConfigured()) return mockGetHeatmap();
  const live = await getBackendDashboardHeatmap();
  return live && live.length > 0 ? live : mockGetHeatmap();
}

export async function getRegionDetail(raId: string): Promise<RegionDetail | null> {
  if (!isBackendConfigured()) return mockGetRegionDetail(raId);
  const live = await getBackendDashboardRegion(raId);
  // Empty 24h windows are legitimate, so only fall back on transport failure.
  return live ?? mockGetRegionDetail(raId);
}

export async function getAttentionUnits(): Promise<AttentionUnit[]> {
  if (!isBackendConfigured()) return mockGetAttentionUnits();
  const live = await getBackendDashboardAttention();
  return live && live.length > 0 ? live : mockGetAttentionUnits();
}

export async function getUnitDetail(unitId: string): Promise<UnitDetail | null> {
  if (!isBackendConfigured()) return mockGetUnitDetail(unitId);
  const live = await getBackendDashboardUnit(unitId);
  // 404 from the backend (returned as `null` by backendFetch) is propagated
  // by trying the mock fallback — keeps preview/offline parity with prod.
  return live ?? mockGetUnitDetail(unitId);
}

export async function getTopics(): Promise<TopicSlice[]> {
  if (!isBackendConfigured()) return mockGetTopics();
  const live = await getBackendDashboardTopics();
  return live && live.length > 0 ? live : mockGetTopics();
}

export async function getTimeSeries(hours = 24): Promise<TimeSeriesPoint[]> {
  if (!isBackendConfigured()) return mockGetTimeSeries(hours);
  const live = await getBackendDashboardTimeseries(hours);
  return live && live.length > 0 ? live : mockGetTimeSeries(hours);
}

export async function getAlerts(): Promise<AlertEvent[]> {
  if (!isBackendConfigured()) return mockGetAlerts();
  const live = await getBackendDashboardAlerts();
  // Alerts can legitimately be empty (no anomalies) — only fall back when the
  // backend call itself failed (returned null), not on empty arrays.
  return live ?? mockGetAlerts();
}

export async function getPipelineHealth(): Promise<PipelineHealth> {
  if (!isBackendConfigured()) {
    return mockGetPipelineHealth();
  }

  // Prefer the dashboard health endpoint (Feature 002) which includes p95
  // latency and last successful ingestion in a single payload.
  const dashHealth = await getBackendDashboardHealth();
  if (dashHealth) return dashHealth;

  // Fallback: derive a synthetic health snapshot from /health + /metrics.
  const [health, metrics] = await Promise.all([getBackendHealth(), getBackendMetrics()]);
  if (!health) {
    return mockGetPipelineHealth();
  }

  const latencyP95Seconds = metrics ? metrics.p95_latency_ms / 1000 : 0;
  const lastIngestion = metrics?.updated_at ?? new Date().toISOString();

  let status: PipelineHealth["status"] = health.status === "ok" ? "ok" : "down";
  if (status === "ok" && latencyP95Seconds > LATENCY_THRESHOLD_SECONDS) {
    status = "degraded";
  }

  const message =
    status === "degraded"
      ? `p95 latency ${Math.round(latencyP95Seconds)}s above ${LATENCY_THRESHOLD_SECONDS}s threshold`
      : undefined;

  return {
    status,
    latencyP95Seconds,
    thresholdSeconds: LATENCY_THRESHOLD_SECONDS,
    lastSuccessfulIngestionAt: lastIngestion,
    message,
  };
}
