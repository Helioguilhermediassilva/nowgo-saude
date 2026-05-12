import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { getAttentionUnits } from "@/lib/dashboard-server";
import type { AttentionUnit, Severity } from "@/lib/types";

export const dynamic = "force-dynamic";

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

export default async function UnitsIndexPage() {
  const items: AttentionUnit[] = await getAttentionUnits();
  const sorted = [...items].sort((a, b) => b.attentionScore - a.attentionScore);
  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <header className="flex items-baseline justify-between gap-2">
          <div>
            <h2 className="text-sm font-semibold">Unidades em atenção crítica</h2>
            <p className="text-[11px] text-muted-foreground">
              Priorização por score de atenção · crescimento vs baseline 14d
            </p>
          </div>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            {items.length} unidades
          </span>
        </header>
        <ul className="flex flex-col divide-y divide-border">
          {sorted.map((u) => (
            <li key={u.unitId}>
              <Link
                href={`/units/${encodeURIComponent(u.unitId)}`}
                className="grid grid-cols-[auto_1fr_auto] items-center gap-3 py-2.5 hover:bg-muted/40"
              >
                <span
                  className={`grid size-9 place-items-center rounded-md border text-sm font-semibold tabular-nums ${SEVERITY_STYLES[u.severity]}`}
                  title={`Severidade ${SEVERITY_LABEL[u.severity]}`}
                >
                  {u.attentionScore}
                </span>
                <div className="flex min-w-0 flex-col">
                  <span className="truncate text-sm font-medium">{u.name}</span>
                  <span className="truncate text-[11px] text-muted-foreground">
                    {u.raName} · +{u.growthPct}% · {u.eventCount24h} eventos · {u.reason}
                  </span>
                </div>
                <ChevronRight className="size-4 text-muted-foreground" />
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
