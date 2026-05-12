import { NextResponse, type NextRequest } from "next/server";
import { getAlertsPage } from "@/lib/dashboard-server";
import type { AlertFilters, AlertStatus, OperationalTopic, Severity } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SEVERITY_VALUES = new Set<Severity>(["critical", "high", "medium", "low"]);
const STATUS_VALUES = new Set<AlertStatus>(["open", "acknowledged", "resolved"]);
const TOPIC_VALUES = new Set<OperationalTopic>([
  "fila",
  "infraestrutura",
  "atendimento",
  "medicamento",
  "agendamento",
  "outros",
]);

export async function GET(request: NextRequest) {
  const sp = request.nextUrl.searchParams;
  const severities = sp.getAll("severity").filter((v): v is Severity =>
    SEVERITY_VALUES.has(v as Severity),
  );
  const statuses = sp.getAll("status").filter((v): v is AlertStatus =>
    STATUS_VALUES.has(v as AlertStatus),
  );
  const topicRaw = sp.get("topic");
  const topic =
    topicRaw && TOPIC_VALUES.has(topicRaw as OperationalTopic)
      ? (topicRaw as OperationalTopic)
      : undefined;
  const raId = sp.get("raId") ?? undefined;
  const limit = Math.min(Math.max(Number.parseInt(sp.get("limit") ?? "12", 10) || 12, 1), 100);
  const offset = Math.max(Number.parseInt(sp.get("offset") ?? "0", 10) || 0, 0);

  const filters: AlertFilters = {
    severity: severities.length ? severities : undefined,
    status: statuses.length ? statuses : undefined,
    topic,
    raId,
    limit,
    offset,
  };

  return NextResponse.json(await getAlertsPage(filters));
}
