import Link from "next/link";
import { notFound } from "next/navigation";
import { ChevronLeft, Minus, TrendingDown, TrendingUp } from "lucide-react";
import { AttentionList } from "@/components/dashboard/attention-list";
import { TimeSeriesChart } from "@/components/dashboard/timeseries-chart";
import { TopicsChart } from "@/components/dashboard/topics-chart";
import { getRegionDetail } from "@/lib/dashboard-server";

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

function pressureBg(score: number) {
  if (score >= 80) return "bg-destructive/80";
  if (score >= 60) return "bg-orange-500/80";
  if (score >= 40) return "bg-yellow-500/80";
  return "bg-emerald-500/70";
}

function formatDelta(curr: number, prev: number) {
  if (prev === 0) return curr === 0 ? "0%" : "+∞";
  const pct = ((curr - prev) / prev) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

interface PageProps {
  params: Promise<{ code: string }>;
}

export default async function RegionDetailPage({ params }: PageProps) {
  const { code } = await params;
  const raId = decodeURIComponent(code);
  const detail = await getRegionDetail(raId);
  if (!detail) notFound();

  const Trend = TREND_ICON[detail.trend];
  const delta = formatDelta(detail.eventCount24h, detail.eventCountPrev24h);

  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <nav className="flex items-center gap-2 text-xs text-muted-foreground">
        <Link
          href="/ra"
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 hover:bg-muted/40"
        >
          <ChevronLeft className="size-3" />
          Regiões
        </Link>
        <span aria-hidden="true">·</span>
        <span>{detail.raId}</span>
      </nav>

      <header className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <div className="flex items-baseline justify-between gap-2">
          <div>
            <h1 className="text-base font-semibold">{detail.raName}</h1>
            <p className="text-[11px] text-muted-foreground">
              {detail.raId} · população {detail.population.toLocaleString("pt-BR")}
            </p>
          </div>
          <span className="flex items-center gap-1 text-xs tabular-nums text-muted-foreground">
            <Trend className="size-3" />
            {detail.pressureScore}
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
              Score de pressão
            </span>
            <div className="h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className={`h-full ${pressureBg(detail.pressureScore)}`}
                style={{ width: `${detail.pressureScore}%` }}
                aria-label={`Score ${detail.pressureScore}`}
              />
            </div>
            <span className="text-[11px] text-muted-foreground">
              {detail.pressureScore} / 100
            </span>
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
          <div className="flex flex-col gap-1 rounded-md border border-border bg-muted/20 p-2">
            <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
              Unidades em atenção
            </span>
            <span className="text-lg font-semibold tabular-nums">{detail.units.length}</span>
            <span className="text-[11px] text-muted-foreground">na RA</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TimeSeriesChart items={detail.timeseries} />
        <TopicsChart items={detail.topics} />
      </div>

      <AttentionList items={detail.units} />
    </main>
  );
}
