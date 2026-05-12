// Domain types for the Command Center Dashboard.
// Aligned with specs/002-command-center-dashboard/spec.md key entities.

export type SmartCityFramework = "ISO 37120" | "ITU-T Y.4900" | "IMD Smart City";

export type Severity = "low" | "medium" | "high" | "critical";

export type Sentiment = "positive" | "neutral" | "negative";

export type OperationalTopic =
  | "fila"
  | "infraestrutura"
  | "atendimento"
  | "medicamento"
  | "agendamento"
  | "outros";

export interface KPI {
  id: string;
  name: string;
  value: number;
  unit: string;
  delta?: number; // variation vs previous period (percent)
  framework: SmartCityFramework;
  reference: string; // e.g. "ISO 37120 §15.1"
  source: string; // e.g. "OuvidorSUS + X/Twitter"
  updatedAt: string; // ISO 8601
}

export interface RegionPressure {
  raId: string; // Região Administrativa code (e.g. "RA-01")
  raName: string;
  pressureScore: number; // 0..100
  eventCount: number;
  topTopic: OperationalTopic;
  trend: "up" | "down" | "stable";
}

export interface AttentionUnit {
  unitId: string;
  name: string;
  raName: string;
  attentionScore: number; // 0..100
  severity: Severity;
  reason: string; // human-readable rationale
  growthPct: number; // % growth vs baseline
  eventCount24h: number;
}

export interface TimeSeriesPoint {
  ts: string; // ISO 8601
  value: number;
}

export interface TopicSlice {
  topic: OperationalTopic;
  count: number;
  pct: number;
}

export interface AlertEvent {
  id: string;
  ruleName: string;
  severity: Severity;
  triggeredAt: string;
  scope: string; // e.g. "RA Ceilândia"
  message: string;
  status: "open" | "acknowledged" | "resolved";
}

export interface PipelineHealth {
  status: "ok" | "degraded" | "down";
  latencyP95Seconds: number;
  thresholdSeconds: number;
  lastSuccessfulIngestionAt: string;
  message?: string;
}

// Region drill-down (Feature 002 §G2.2): joins heatmap, topic mix,
// hourly series, and the attention units inside a single RA.
export interface RegionDetail {
  raId: string;
  raName: string;
  population: number;
  pressureScore: number;
  eventCount24h: number;
  eventCountPrev24h: number;
  topTopic: OperationalTopic;
  trend: "up" | "down" | "stable";
  topics: TopicSlice[];
  timeseries: TimeSeriesPoint[];
  units: AttentionUnit[];
}

// Raw shapes returned by the FastAPI backend (Feature 001).
export interface PipelineHealthBackend {
  status: string;
  environment: string;
}

export interface MetricsSummary {
  events_per_minute: number;
  p95_latency_ms: number;
  dlq_depth: number;
  anonymization_failures_24h: number;
  updated_at: string;
}
