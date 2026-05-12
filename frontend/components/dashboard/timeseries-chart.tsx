"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TimeSeriesPoint } from "@/lib/types";

interface TimeSeriesChartProps {
  items: TimeSeriesPoint[];
  mode?: "hour" | "day";
  title?: string;
  description?: string;
}

export function TimeSeriesChart({
  items,
  mode = "hour",
  title = "Eventos por hora · 24h",
  description = "Volume agregado de menções e queixas operacionais",
}: TimeSeriesChartProps) {
  const data = items.map((p) => ({
    label:
      mode === "day"
        ? new Date(p.ts).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
          })
        : new Date(p.ts).toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
    value: p.value,
  }));
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header>
        <h2 className="text-sm font-semibold">{title}</h2>
        <p className="text-[11px] text-muted-foreground">{description}</p>
      </header>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="ts-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.35} />
                <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              minTickGap={24}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              width={32}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                borderRadius: 8,
                fontSize: 12,
              }}
              labelStyle={{ color: "hsl(var(--muted-foreground))" }}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              fill="url(#ts-fill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
