// Feature 002 §G2.4 — pagination controls for the /alerts page.
// Server component: renders prev/next links that preserve the current
// URL query (filters) and only mutate the `offset` param.

import Link from "next/link";

function buildHref(params: URLSearchParams, offset: number): string {
  const next = new URLSearchParams(params);
  if (offset <= 0) next.delete("offset");
  else next.set("offset", String(offset));
  const qs = next.toString();
  return qs ? `?${qs}` : "?";
}

export function AlertsPagination({
  total,
  limit,
  offset,
  currentParams,
}: {
  total: number;
  limit: number;
  offset: number;
  currentParams: URLSearchParams;
}) {
  const page = Math.floor(offset / limit) + 1;
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const hasPrev = offset > 0;
  const hasNext = offset + limit < total;
  const start = total === 0 ? 0 : offset + 1;
  const end = Math.min(offset + limit, total);

  return (
    <nav
      aria-label="Paginação de alertas"
      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card px-4 py-2.5"
    >
      <span className="text-[11px] text-muted-foreground">
        {total === 0
          ? "Nenhum resultado"
          : `Mostrando ${start}–${end} de ${total} · página ${page}/${pageCount}`}
      </span>
      <div className="flex items-center gap-2">
        <PageLink
          href={buildHref(currentParams, Math.max(0, offset - limit))}
          enabled={hasPrev}
          label="Anterior"
        />
        <PageLink
          href={buildHref(currentParams, offset + limit)}
          enabled={hasNext}
          label="Próxima"
        />
      </div>
    </nav>
  );
}

function PageLink({
  href,
  enabled,
  label,
}: {
  href: string;
  enabled: boolean;
  label: string;
}) {
  if (!enabled) {
    return (
      <span
        aria-disabled
        className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground opacity-50"
      >
        {label}
      </span>
    );
  }
  return (
    <Link
      href={href}
      className="rounded-md border border-border px-2.5 py-1 text-[11px] text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
    >
      {label}
    </Link>
  );
}
