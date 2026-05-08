import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import type { RegionPressure } from "@/lib/types";

function pressureBg(score: number) {
  if (score >= 80) return "bg-destructive/80";
  if (score >= 60) return "bg-orange-500/80";
  if (score >= 40) return "bg-yellow-500/80";
  return "bg-emerald-500/70";
}

const TREND_ICON = { up: TrendingUp, down: TrendingDown, stable: Minus } as const;

export function HeatmapRegions({ items }: { items: RegionPressure[] }) {
  const sorted = [...items].sort((a, b) => b.pressureScore - a.pressureScore);
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">Pressão por Região Administrativa</h2>
          <p className="text-[11px] text-muted-foreground">
            Score combinado (volume + sentimento + anomalia) · janela 24h
          </p>
        </div>
        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
          {items.length} RAs
        </span>
      </header>
      <ol className="flex flex-col gap-1.5">
        {sorted.map((r) => {
          const Trend = TREND_ICON[r.trend];
          return (
            <li
              key={r.raId}
              className="grid grid-cols-[1fr_auto] items-center gap-3 rounded-md px-1 py-1 hover:bg-muted/40"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="font-medium">{r.raName}</span>
                  <span className="text-muted-foreground">
                    {r.eventCount.toLocaleString("pt-BR")} eventos · {r.topTopic}
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full ${pressureBg(r.pressureScore)}`}
                    style={{ width: `${r.pressureScore}%` }}
                    aria-label={`Score ${r.pressureScore}`}
                  />
                </div>
              </div>
              <span className="flex items-center gap-1 text-xs tabular-nums text-muted-foreground">
                <Trend className="size-3" />
                {r.pressureScore}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
