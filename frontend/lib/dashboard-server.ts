// Server-side data accessors used by the dashboard during SSR.
// When BACKEND_API_URL is configured, getPipelineHealth bridges to the real
// FastAPI backend (Feature 001) — using /health and /api/v1/metrics — and
// falls back to the mock layer on any failure or when the env is missing.
// All other accessors keep their mock implementation until the backend
// exposes the corresponding aggregations.

import "server-only";

import { getBackendHealth, getBackendMetrics, isBackendConfigured } from "./backend-client";
import {
  getAlerts as mockGetAlerts,
  getAttentionUnits as mockGetAttentionUnits,
  getHeatmap as mockGetHeatmap,
  getKpis as mockGetKpis,
  getPipelineHealth as mockGetPipelineHealth,
  getTimeSeries as mockGetTimeSeries,
  getTopics as mockGetTopics,
} from "./mock-data";
import type { PipelineHealth } from "./types";

export const getKpis = mockGetKpis;
export const getAttentionUnits = mockGetAttentionUnits;
export const getHeatmap = mockGetHeatmap;
export const getAlerts = mockGetAlerts;
export const getTimeSeries = mockGetTimeSeries;
export const getTopics = mockGetTopics;

const LATENCY_THRESHOLD_SECONDS = 300;

export async function getPipelineHealth(): Promise<PipelineHealth> {
  if (!isBackendConfigured()) {
    return mockGetPipelineHealth();
  }

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
