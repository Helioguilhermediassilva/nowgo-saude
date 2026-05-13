import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronLeft, Minus, TrendingDown, TrendingUp } from "lucide-react";
import { TimeSeriesChart } from "@/components/dashboard/timeseries-chart";
import { TopicsChart } from "@/components/dashboard/topics-chart";
import { getUnitDetail } from "@/lib/dashboard-server";
import type { Severity } from "@/lib/types";

export const dynamic = "force-dynamic";

const TREND_ICON = { up: TrendingUp, down: TrendingDown, stable: Minus } as const;

const TOPIC_LABEL: Record<string, string> = {
  fila: "Fila",
  atendimento: "Atendimento",
  medicamento: "Medicamento",
  agendamento: "Agendamento",
  infraestrutura: "Infraestrutura",
  outros: "Outros",
};

const SEVERITY_STYLES: Record<Severity, string> = {
  critical:
    "border-destructive/40 bg-destructive/10 text-destructive dark:bg-destructive/20",
  high: "border-orange-500/40 bg-orange-500/10 text-orange-700 dark:text-orange-300",
  medium: "border-yellow-500/40 bg-yellow-500/10 text-yellow-800 dark:text-yellow-300",
  low: "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Média",
  low: "Baixa",
};

const SENTIMENT_LABEL: Record<number, string> = {
  [-2]: "muito negativo",
  [-1]: "negativo",
  0: "neutro",
  1: "positivo",
  2: "muito positivo",
};

function formatDelta(curr: number, prev: number) {
  if (prev === 0) return curr === 0 ? "0%" : "+∞";
  const pct = ((curr - prev) / prev) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function UnitDetailPage({ params }: PageProps) {
  const { id } = await params;
  const unitId = decodeURIComponent(id);
  const detail = await getUnitDetail(unitId);
  if (!detail) notFound();

  const Trend = TREND_ICON[detail.trend];
  const delta = formatDelta(detail.eventCount24h, detail.eventCountPrev24h);

  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <nav className="flex items-center gap-2 text-xs text-muted-foreground">
        <Link
          href="/units"
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 hover:bg-muted/40"
        >
          <ChevronLeft className="size-3" />
          Unidades
        </Link>
        <span aria-hidden="true">·</span>
        {detail.raId ? (
          <Link href={`/ra/${encodeURIComponent(detail.raId)}`} className="hover:underline">
            {detail.raName}
          </Link>
        ) : (
          <span>{detail.raName}</span>
        )}
        <span aria-hidden="true">·</span>
        <span>{detail.unitId}</span>
      </nav>

      <header className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <div className="flex items-baseline justify-between gap-2">
          <div>
            <h1 className="text-base font-semibold">{detail.name}</h1>
            <p className="text-[11px] text-muted-foreground">
              {detail.raName} · {detail.unitId}
            </p>
          </div>
          <span
            className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[detail.severity]}`}
            title={`Severidade ${SEVERITY_LABEL[detail.severity]}`}
          >
            <Trend className="size-3" />
            {detail.attentionScore} · {SEVERITY_LABEL[detail.severity]}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="flex flex-col gap-1 rounded-md border border-border bg-muted/20 p-2">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Eventos 24h
            </span>
            <span className="text-lg font-semibold tabular-nums">
              {detail.eventCount24h.toLocaleString("pt-BR")}
            </span>
            <span className="text-[11px] text-muted-foreground">vs 24h ant.: {delta}</span>
          </div>
          <div className="flex flex-col gap-1 rounded-md border border-border bg-muted/20 p-2">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Eventos 7d
            </span>
            <span className="text-lg font-semibold tabular-nums">
              {detail.eventCount7d.toLocaleString("pt-BR")}
            </span>
            <span className="text-[11px] text-muted-foreground">janela móvel</span>
          </div>
          <div className="flex flex-col gap-1 rounded-md border border-border bg-muted/20 p-2">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Crescimento
            </span>
            <span className="text-lg font-semibold tabular-nums">
              {detail.growthPct >= 0 ? "+" : ""}
              {detail.growthPct}%
            </span>
            <span className="text-[11px] text-muted-foreground">vs baseline 14d</span>
          </div>
          <div className="flex flex-col gap-1 rounded-md border border-border bg-muted/20 p-2">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Tópico dominante
            </span>
            <span className="text-sm font-medium">
              {TOPIC_LABEL[detail.topTopic] ?? detail.topTopic}
            </span>
            <span className="text-[11px] text-muted-foreground">últimas 24h</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TimeSeriesChart
          items={detail.timeseries}
          mode="day"
          title="Eventos por dia · 7d"
          description="Volume diário de menções e queixas operacionais na unidade"
        />
        <TopicsChart items={detail.topics} />
      </div>

      <RecentEventsFeed events={detail.recentEvents} />
    </main>
  );
}

function RecentEventsFeed({
  events,
}: {
  events: import("@/lib/types").RecentEvent[];
}) {
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">Eventos recentes</h2>
          <p className="text-[11px] text-muted-foreground">
            Texto anonimizado · tópico, severidade e sentimento classificados por NLP
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {events.length} eventos
        </span>
      </header>
      {events.length === 0 ? (
        <p className="text-xs text-muted-foreground">Nenhum evento recente registrado.</p>
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {events.map((e) => (
            <li key={e.id} className="flex flex-col gap-1 py-2.5">
              <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                <span>
                  {new Date(e.receivedAt).toLocaleString("pt-BR", {
                    dateStyle: "short",
                    timeStyle: "short",
                  })}
                </span>
                <span className="flex items-center gap-2">
                  <span className="rounded-md border border-border bg-muted/30 px-1.5 py-0.5">
                    {TOPIC_LABEL[e.topic] ?? e.topic}
                  </span>
                  <span>sev {e.severity}</span>
                  <span>· {SENTIMENT_LABEL[e.sentiment] ?? e.sentiment}</span>
                </span>
              </div>
              <p className="text-sm">{e.text}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
