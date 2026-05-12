// Feature 002 §G2.4 — dedicated alerts page with URL-driven filters
// and pagination. All filter state lives in `searchParams` so the page
// is shareable and refreshable.

import { AlertsFilters } from "@/components/dashboard/alerts-filters";
import { AlertsPagination } from "@/components/dashboard/alerts-pagination";
import { AlertsPanel } from "@/components/dashboard/alerts-panel";
import { getAlertsPage, getHeatmap } from "@/lib/dashboard-server";
import type {
  AlertFilters,
  AlertStatus,
  OperationalTopic,
  Severity,
} from "@/lib/types";

export const dynamic = "force-dynamic";

const SEVERITY_VALUES = new Set<Severity>([
  "critical",
  "high",
  "medium",
  "low",
]);
const STATUS_VALUES = new Set<AlertStatus>([
  "open",
  "acknowledged",
  "resolved",
]);
const TOPIC_VALUES = new Set<OperationalTopic>([
  "fila",
  "infraestrutura",
  "atendimento",
  "medicamento",
  "agendamento",
  "outros",
]);

const DEFAULT_LIMIT = 20;
const MAX_LIMIT = 100;

function toArray(v: string | string[] | undefined): string[] {
  if (v === undefined) return [];
  return Array.isArray(v) ? v : [v];
}

function parseSeverities(raw: string | string[] | undefined): Severity[] {
  return toArray(raw).filter((s): s is Severity =>
    SEVERITY_VALUES.has(s as Severity),
  );
}

function parseStatuses(raw: string | string[] | undefined): AlertStatus[] {
  return toArray(raw).filter((s): s is AlertStatus =>
    STATUS_VALUES.has(s as AlertStatus),
  );
}

function parseTopic(raw: string | string[] | undefined): OperationalTopic | null {
  const v = toArray(raw)[0];
  return v && TOPIC_VALUES.has(v as OperationalTopic)
    ? (v as OperationalTopic)
    : null;
}

function parseRaId(raw: string | string[] | undefined): string | null {
  const v = toArray(raw)[0];
  return v && /^RA-[A-Z0-9]{1,5}$/.test(v) ? v : null;
}

function parseNonNegativeInt(
  raw: string | string[] | undefined,
  fallback: number,
  max: number,
): number {
  const v = toArray(raw)[0];
  if (!v) return fallback;
  const n = Number.parseInt(v, 10);
  if (!Number.isFinite(n) || n < 0) return fallback;
  return Math.min(n, max);
}

type SearchParams = Record<string, string | string[] | undefined>;

export default async function AlertsIndexPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const sp = (await searchParams) ?? {};

  const severities = parseSeverities(sp.severity);
  const statuses = parseStatuses(sp.status);
  const topic = parseTopic(sp.topic);
  const raId = parseRaId(sp.raId);
  const limit = parseNonNegativeInt(sp.limit, DEFAULT_LIMIT, MAX_LIMIT) || DEFAULT_LIMIT;
  const offset = parseNonNegativeInt(sp.offset, 0, 10_000);

  const filters: AlertFilters = {
    severity: severities.length ? severities : undefined,
    status: statuses.length ? statuses : undefined,
    topic: topic ?? undefined,
    raId: raId ?? undefined,
    limit,
    offset,
  };

  const [page, heatmap] = await Promise.all([
    getAlertsPage(filters),
    getHeatmap(),
  ]);

  // Build the canonical params so client filters and pagination links
  // operate on the same baseline (drops unknown keys/values).
  const canonical = new URLSearchParams();
  for (const s of severities) canonical.append("severity", s);
  for (const s of statuses) canonical.append("status", s);
  if (topic) canonical.set("topic", topic);
  if (raId) canonical.set("raId", raId);
  if (limit !== DEFAULT_LIMIT) canonical.set("limit", String(limit));
  if (offset > 0) canonical.set("offset", String(offset));

  const raOptions = heatmap
    .map((r) => ({ id: r.raId, name: r.raName }))
    .sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));

  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold">Alertas</h1>
        <p className="text-[12px] text-muted-foreground">
          Sinais sintetizados a partir do heatmap regional e das unidades em
          atenção. Use os filtros para inspecionar severidade, status, tópico
          ou Região Administrativa.
        </p>
      </header>
      <AlertsFilters
        selectedSeverities={severities}
        selectedStatuses={statuses}
        selectedTopic={topic}
        selectedRaId={raId}
        raOptions={raOptions}
      />
      <AlertsPanel
        items={page.items}
        severityCounts={page.severityCounts}
        subtitle={`Total filtrado: ${page.total}`}
      />
      <AlertsPagination
        total={page.total}
        limit={page.limit}
        offset={page.offset}
        currentParams={canonical}
      />
    </main>
  );
}
