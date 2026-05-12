import { AlertTriangle, BellRing, CheckCircle2 } from "lucide-react";
import type { AlertEvent, AlertSeverityCounts } from "@/lib/types";

const STATUS_ICON = {
  open: BellRing,
  acknowledged: AlertTriangle,
  resolved: CheckCircle2,
} as const;

const SEV_DOT: Record<AlertEvent["severity"], string> = {
  critical: "bg-destructive",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-emerald-500",
};

const TOPIC_LABEL: Record<NonNullable<AlertEvent["topic"]>, string> = {
  fila: "Fila",
  infraestrutura: "Infraestrutura",
  atendimento: "Atendimento",
  medicamento: "Medicamento",
  agendamento: "Agendamento",
  outros: "Outros",
};

export function AlertsPanel({
  items,
  title = "Alertas operacionais",
  subtitle = "Disparos de regras configuradas no Worker de anomalias",
  severityCounts,
  emptyMessage = "Nenhum alerta para os filtros atuais.",
}: {
  items: AlertEvent[];
  title?: string;
  subtitle?: string;
  severityCounts?: AlertSeverityCounts;
  emptyMessage?: string;
}) {
  const activeCount = items.filter((a) => a.status !== "resolved").length;
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">{title}</h2>
          <p className="text-[11px] text-muted-foreground">{subtitle}</p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {activeCount} ativos
        </span>
      </header>
      {severityCounts && (
        <div className="flex flex-wrap gap-2 text-[10px] uppercase tracking-wide text-muted-foreground">
          <SeverityBadge dot="bg-destructive" label="Crítico" count={severityCounts.critical} />
          <SeverityBadge dot="bg-orange-500" label="Alto" count={severityCounts.high} />
          <SeverityBadge dot="bg-yellow-500" label="Médio" count={severityCounts.medium} />
          <SeverityBadge dot="bg-emerald-500" label="Baixo" count={severityCounts.low} />
        </div>
      )}
      {items.length === 0 ? (
        <p className="py-6 text-center text-[11px] text-muted-foreground">{emptyMessage}</p>
      ) : (
        <ul className="flex flex-col divide-y divide-border">
          {items.map((a) => {
            const Icon = STATUS_ICON[a.status];
            return (
              <li key={a.id} className="flex items-start gap-3 py-2.5">
                <Icon className="mt-0.5 size-4 text-muted-foreground" />
                <div className="flex min-w-0 flex-1 flex-col">
                  <div className="flex items-center gap-2">
                    <span className={`size-2 rounded-full ${SEV_DOT[a.severity]}`} />
                    <span className="truncate text-sm font-medium">{a.ruleName}</span>
                  </div>
                  <span className="text-[11px] text-muted-foreground">{a.message}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {a.scope}
                    {a.topic ? ` · ${TOPIC_LABEL[a.topic]}` : ""} ·{" "}
                    {new Date(a.triggeredAt).toLocaleTimeString("pt-BR", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function SeverityBadge({ dot, label, count }: { dot: string; label: string; count: number }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-border px-2 py-0.5">
      <span className={`size-1.5 rounded-full ${dot}`} />
      {label}
      <span className="font-medium text-foreground">{count}</span>
    </span>
  );
}
