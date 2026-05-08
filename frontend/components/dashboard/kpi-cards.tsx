import { ArrowDownRight, ArrowUpRight, Info } from "lucide-react";
import type { KPI } from "@/lib/types";

function deltaColor(delta?: number) {
  if (delta == null) return "text-muted-foreground";
  // For most operational KPIs (waits, complaints, attention units),
  // increases are negative outcomes. Coverage KPI is the opposite, but
  // for this MVP we keep the visual cue conservative and neutral.
  return delta > 0
    ? "text-destructive"
    : delta < 0
      ? "text-emerald-600 dark:text-emerald-400"
      : "text-muted-foreground";
}

export function KpiCards({ items }: { items: KPI[] }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((k) => {
        const Icon = (k.delta ?? 0) >= 0 ? ArrowUpRight : ArrowDownRight;
        return (
          <article
            key={k.id}
            className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4"
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-xs font-medium text-muted-foreground">{k.name}</h3>
              <span
                title={`${k.framework} · ${k.reference}`}
                className="inline-flex items-center gap-1 rounded-md border border-border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground"
              >
                <Info className="size-3" />
                {k.framework}
              </span>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-semibold tabular-nums">
                {k.value.toLocaleString("pt-BR")}
              </span>
              <span className="text-xs text-muted-foreground">{k.unit}</span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              {k.delta != null ? (
                <span className={`inline-flex items-center gap-1 ${deltaColor(k.delta)}`}>
                  <Icon className="size-3" />
                  {Math.abs(k.delta).toFixed(1)}% vs período anterior
                </span>
              ) : (
                <span className="text-muted-foreground">—</span>
              )}
              <span className="truncate text-muted-foreground" title={k.source}>
                {k.source}
              </span>
            </div>
          </article>
        );
      })}
    </div>
  );
}
