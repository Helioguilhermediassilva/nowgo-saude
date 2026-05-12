// Mock data generator for the dashboard. Will be replaced by real API
// calls into backend feature 001/002 once those are deployed.

import type {
  AlertEvent,
  AttentionUnit,
  KPI,
  PipelineHealth,
  RegionDetail,
  RegionPressure,
  TimeSeriesPoint,
  TopicSlice,
} from "./types";

const RAS = [
  { id: "RA-I", name: "Plano Piloto" },
  { id: "RA-IX", name: "Ceilândia" },
  { id: "RA-III", name: "Taguatinga" },
  { id: "RA-X", name: "Guará" },
  { id: "RA-VIII", name: "Núcleo Bandeirante" },
  { id: "RA-XII", name: "Samambaia" },
  { id: "RA-XIII", name: "Santa Maria" },
  { id: "RA-XV", name: "Recanto das Emas" },
  { id: "RA-XVI", name: "Lago Sul" },
  { id: "RA-XVII", name: "Riacho Fundo" },
  { id: "RA-XXIX", name: "Sol Nascente / Pôr do Sol" },
  { id: "RA-XX", name: "Águas Claras" },
];

// Deterministic PRNG so renders are stable across requests.
function mulberry32(seed: number) {
  let s = seed;
  return () => {
    s = (s + 0x6d2b79f5) | 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rng = mulberry32(20260508);

export function getKpis(): KPI[] {
  const now = new Date().toISOString();
  return [
    {
      id: "kpi.queue.wait_p95",
      name: "Tempo de espera p95 (UPAs)",
      value: 142,
      unit: "min",
      delta: 8.4,
      framework: "ISO 37120",
      reference: "ISO 37120 §15.4 — tempo médio de atendimento",
      source: "OuvidorSUS + sensores operacionais",
      updatedAt: now,
    },
    {
      id: "kpi.complaint.rate_24h",
      name: "Reclamações por 100k hab. (24h)",
      value: 38.2,
      unit: "/100k",
      delta: 12.7,
      framework: "IMD Smart City",
      reference: "IMD §Saúde — percepção do residente",
      source: "OuvidorSUS + X/Twitter",
      updatedAt: now,
    },
    {
      id: "kpi.coverage.appointment",
      name: "Cobertura de agendamento (semana)",
      value: 73.5,
      unit: "%",
      delta: -2.1,
      framework: "ITU-T Y.4900",
      reference: "ITU-T Y.4900 §7.2 — eficácia do serviço",
      source: "Pipeline operacional",
      updatedAt: now,
    },
    {
      id: "kpi.unit.attention_count",
      name: "Unidades em atenção crítica",
      value: 7,
      unit: "unid.",
      delta: 16.7,
      framework: "ISO 37120",
      reference: "ISO 37120 §15.5 — leitos disponíveis",
      source: "Worker de anomalias",
      updatedAt: now,
    },
  ];
}

export function getHeatmap(): RegionPressure[] {
  const topics: RegionPressure["topTopic"][] = [
    "fila",
    "atendimento",
    "medicamento",
    "infraestrutura",
    "agendamento",
  ];
  return RAS.map((ra, i) => ({
    raId: ra.id,
    raName: ra.name,
    pressureScore: Math.round(20 + rng() * 75),
    eventCount: Math.round(40 + rng() * 480),
    topTopic: topics[i % topics.length] as RegionPressure["topTopic"],
    trend: rng() > 0.6 ? "up" : rng() > 0.4 ? "stable" : "down",
  }));
}

export function getAttentionUnits(): AttentionUnit[] {
  const units = [
    { id: "u-001", name: "UPA Ceilândia", ra: "Ceilândia" },
    { id: "u-002", name: "Hospital Regional de Samambaia", ra: "Samambaia" },
    { id: "u-003", name: "UBS 3 Sol Nascente", ra: "Sol Nascente / Pôr do Sol" },
    { id: "u-004", name: "Hospital Materno-Infantil de Brasília", ra: "Plano Piloto" },
    { id: "u-005", name: "UPA Recanto das Emas", ra: "Recanto das Emas" },
    { id: "u-006", name: "UBS 2 Riacho Fundo", ra: "Riacho Fundo" },
    { id: "u-007", name: "Hospital Regional de Taguatinga", ra: "Taguatinga" },
  ];
  const reasons = [
    "Crescimento de 40% em queixas de fila vs média 14d",
    "Anomalia em reclamações de medicamento em falta",
    "Picos consecutivos de atendimento p95 acima do baseline",
    "Aumento de menções a infraestrutura precária",
  ];
  return units.map((u, i) => {
    const score = Math.round(70 + rng() * 28);
    return {
      unitId: u.id,
      name: u.name,
      raName: u.ra,
      attentionScore: score,
      severity: score >= 90 ? "critical" : score >= 80 ? "high" : "medium",
      reason: reasons[i % reasons.length] as string,
      growthPct: Math.round(15 + rng() * 60),
      eventCount24h: Math.round(20 + rng() * 220),
    };
  });
}

export function getTimeSeries(hours = 24): TimeSeriesPoint[] {
  const out: TimeSeriesPoint[] = [];
  const now = Date.now();
  let v = 80 + rng() * 40;
  for (let i = hours; i >= 0; i--) {
    v = Math.max(20, Math.min(280, v + (rng() - 0.45) * 30));
    out.push({
      ts: new Date(now - i * 3600 * 1000).toISOString(),
      value: Math.round(v),
    });
  }
  return out;
}

export function getTopics(): TopicSlice[] {
  const raw: TopicSlice[] = [
    { topic: "fila", count: 482, pct: 0 },
    { topic: "atendimento", count: 311, pct: 0 },
    { topic: "medicamento", count: 226, pct: 0 },
    { topic: "agendamento", count: 188, pct: 0 },
    { topic: "infraestrutura", count: 142, pct: 0 },
    { topic: "outros", count: 97, pct: 0 },
  ];
  const total = raw.reduce((s, t) => s + t.count, 0);
  return raw.map((t) => ({ ...t, pct: Math.round((t.count / total) * 1000) / 10 }));
}

export function getAlerts(): AlertEvent[] {
  const now = Date.now();
  return [
    {
      id: "a-001",
      ruleName: "Fila > limiar (Ceilândia)",
      severity: "high",
      triggeredAt: new Date(now - 8 * 60_000).toISOString(),
      scope: "RA Ceilândia",
      message: "Reclamações de fila acima do limiar de 30/h por 2 janelas seguidas",
      status: "open",
    },
    {
      id: "a-002",
      ruleName: "Anomalia medicamento (Sol Nascente)",
      severity: "critical",
      triggeredAt: new Date(now - 23 * 60_000).toISOString(),
      scope: "UBS 3 Sol Nascente",
      message: "Crescimento atípico (+58%) em queixas sobre medicamento em falta",
      status: "open",
    },
    {
      id: "a-003",
      ruleName: "Pressão sustentada (Samambaia)",
      severity: "medium",
      triggeredAt: new Date(now - 3 * 3600_000).toISOString(),
      scope: "RA Samambaia",
      message: "Score de pressão acima de 70 por 3 janelas consecutivas",
      status: "acknowledged",
    },
  ];
}

export function getPipelineHealth(): PipelineHealth {
  return {
    status: "ok",
    latencyP95Seconds: 47,
    thresholdSeconds: 300,
    lastSuccessfulIngestionAt: new Date(Date.now() - 12_000).toISOString(),
  };
}

// Derived region drill-down used as fallback when the backend cannot be
// reached. Picks the heatmap row matching `raId` and seeds the drill-down
// from the existing topics/timeseries/attention mocks.
export function getRegionDetail(raId: string): RegionDetail | null {
  const ra = RAS.find((r) => r.id === raId);
  if (!ra) return null;
  const pressure = getHeatmap().find((r) => r.raId === raId);
  const allTopics = getTopics();
  const total24h = Math.round(60 + rng() * 240);
  // Scale the global topic mix to the RA scope.
  const topics: TopicSlice[] = allTopics.map((t) => {
    const count = Math.max(1, Math.round((t.pct / 100) * total24h));
    return { topic: t.topic, count, pct: t.pct };
  });
  const units = getAttentionUnits().filter((u) => u.raName === ra.name);
  return {
    raId: ra.id,
    raName: ra.name,
    population: 100_000 + Math.round(rng() * 400_000),
    pressureScore: pressure?.pressureScore ?? Math.round(20 + rng() * 75),
    eventCount24h: total24h,
    eventCountPrev24h: Math.round(total24h * (0.6 + rng() * 0.6)),
    topTopic: pressure?.topTopic ?? "fila",
    trend: pressure?.trend ?? "stable",
    topics,
    timeseries: getTimeSeries(24),
    units,
  };
}
