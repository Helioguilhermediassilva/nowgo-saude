"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TopicSlice } from "@/lib/types";

const PALETTE = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
  "hsl(var(--muted-foreground))",
];

const TOPIC_LABEL: Record<TopicSlice["topic"], string> = {
  fila: "Fila",
  atendimento: "Atendimento",
  medicamento: "Medicamento",
  agendamento: "Agendamento",
  infraestrutura: "Infraestrutura",
  outros: "Outros",
};

export function TopicsChart({ items }: { items: TopicSlice[] }) {
  const data = items.map((t) => ({
    label: TOPIC_LABEL[t.topic],
    value: t.count,
    pct: t.pct,
  }));
  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header>
        <h2 className="text-sm font-semibold">Tópicos operacionais · 24h</h2>
        <p className="text-[11px] text-muted-foreground">
          Distribuição de temas extraídos por NLP em mensagens cidadãs
        </p>
      </header>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
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
              formatter={(value, _name, item) => {
                const v = typeof value === "number" ? value : Number(value ?? 0);
                const pct = (item?.payload as { pct?: number } | undefined)?.pct ?? 0;
                return [`${v.toLocaleString("pt-BR")} (${pct}%)`, "Eventos"];
              }}
            />
            <Bar dataKey="value" radius={[6, 6, 0, 0]}>
              {data.map((_, i) => (
                <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
