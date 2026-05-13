"use client";

// Feature 002 §G2.4 — client-side filter controls for the /alerts page.
// Mutates the URL search params via Next router; the server component
// re-renders with the updated `searchParams`, so all filter state lives
// in the URL (shareable, refreshable, back/forward-friendly).

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";

import type {
  AlertStatus,
  OperationalTopic,
  Severity,
} from "@/lib/types";

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low"];
const STATUSES: AlertStatus[] = ["open", "acknowledged", "resolved"];
const TOPICS: OperationalTopic[] = [
  "fila",
  "infraestrutura",
  "atendimento",
  "medicamento",
  "agendamento",
  "outros",
];

const SEV_LABEL: Record<Severity, string> = {
  critical: "Crítico",
  high: "Alto",
  medium: "Médio",
  low: "Baixo",
};

const STATUS_LABEL: Record<AlertStatus, string> = {
  open: "Aberto",
  acknowledged: "Reconhecido",
  resolved: "Resolvido",
};

const TOPIC_LABEL: Record<OperationalTopic, string> = {
  fila: "Fila",
  infraestrutura: "Infraestrutura",
  atendimento: "Atendimento",
  medicamento: "Medicamento",
  agendamento: "Agendamento",
  outros: "Outros",
};

function Pill({
  active,
  onClick,
  children,
  disabled,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-active={active || undefined}
      className="rounded-full border border-border px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground data-[active]:border-foreground data-[active]:bg-foreground data-[active]:text-background disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}

export function AlertsFilters({
  selectedSeverities,
  selectedStatuses,
  selectedTopic,
  selectedRaId,
  raOptions,
}: {
  selectedSeverities: Severity[];
  selectedStatuses: AlertStatus[];
  selectedTopic: OperationalTopic | null;
  selectedRaId: string | null;
  raOptions: { id: string; name: string }[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();
  const [pending, startTransition] = useTransition();

  function push(next: URLSearchParams) {
    // Reset to first page whenever filters change.
    next.delete("offset");
    startTransition(() => router.replace(`${pathname}?${next.toString()}`));
  }

  function toggleMulti(key: "severity" | "status", value: string) {
    const next = new URLSearchParams(sp);
    const current = next.getAll(key);
    next.delete(key);
    const updated = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value];
    for (const v of updated) next.append(key, v);
    push(next);
  }

  function setSingle(key: "topic" | "raId", value: string | null) {
    const next = new URLSearchParams(sp);
    if (value) next.set(key, value);
    else next.delete(key);
    push(next);
  }

  function clearAll() {
    startTransition(() => router.replace(pathname));
  }

  const hasActive =
    selectedSeverities.length > 0 ||
    selectedStatuses.length > 0 ||
    selectedTopic !== null ||
    selectedRaId !== null;

  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <header className="flex items-baseline justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold">Filtros</h2>
          <p className="text-[11px] text-muted-foreground">
            Severidade, status, RA e tópico operacional. URL é a fonte da verdade.
          </p>
        </div>
        {hasActive && (
          <button
            type="button"
            onClick={clearAll}
            disabled={pending}
            className="text-[11px] text-muted-foreground underline-offset-2 hover:underline disabled:opacity-50"
          >
            Limpar
          </button>
        )}
      </header>

      <FilterRow label="Severidade">
        {SEVERITIES.map((s) => (
          <Pill
            key={s}
            active={selectedSeverities.includes(s)}
            disabled={pending}
            onClick={() => toggleMulti("severity", s)}
          >
            {SEV_LABEL[s]}
          </Pill>
        ))}
      </FilterRow>

      <FilterRow label="Status">
        {STATUSES.map((s) => (
          <Pill
            key={s}
            active={selectedStatuses.includes(s)}
            disabled={pending}
            onClick={() => toggleMulti("status", s)}
          >
            {STATUS_LABEL[s]}
          </Pill>
        ))}
      </FilterRow>

      <FilterRow label="Tópico">
        {TOPICS.map((t) => (
          <Pill
            key={t}
            active={selectedTopic === t}
            disabled={pending}
            onClick={() => setSingle("topic", selectedTopic === t ? null : t)}
          >
            {TOPIC_LABEL[t]}
          </Pill>
        ))}
      </FilterRow>

      <FilterRow label="Região Administrativa">
        {raOptions.map((ra) => (
          <Pill
            key={ra.id}
            active={selectedRaId === ra.id}
            disabled={pending}
            onClick={() => setSingle("raId", selectedRaId === ra.id ? null : ra.id)}
          >
            {ra.name}
          </Pill>
        ))}
      </FilterRow>
    </section>
  );
}

function FilterRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}
