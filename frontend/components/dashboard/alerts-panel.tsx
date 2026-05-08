import { AlertTriangle, BellRing, CheckCircle2 } from "lucide-react";
import type { AlertEvent } from "@/lib/types";

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

export function AlertsPanel({ items }: { items: AlertEvent[] }) {
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">Alertas operacionais</h2>
          <p className="text-[11px] text-muted-foreground">
            Disparos de regras configuradas no Worker de anomalias
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {items.filter((a) => a.status !== "resolved").length} ativos
        </span>
      </header>
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
                  {a.scope} ·{" "}
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
    </section>
  );
}
