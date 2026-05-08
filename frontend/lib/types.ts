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
