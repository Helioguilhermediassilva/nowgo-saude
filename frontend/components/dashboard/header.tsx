import { Bell, RefreshCcw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header() {
  const now = new Date();
  const ts = now.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  return (
    <header className="flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur lg:px-6">
      <div className="flex flex-col leading-tight">
        <h1 className="text-sm font-semibold">Painel Operacional · Distrito Federal</h1>
        <p className="text-[11px] text-muted-foreground">
          Visão consolidada · atualizado {ts}
        </p>
      </div>
      <div className="ml-auto flex items-center gap-2">
        <div className="hidden h-8 items-center gap-1.5 rounded-md border border-border bg-card px-2 text-xs text-muted-foreground md:flex">
          <Search className="size-3.5" />
          <span>Buscar unidade, RA ou tópico…</span>
        </div>
        <Button variant="outline" size="sm" aria-label="Atualizar">
          <RefreshCcw className="size-3.5" />
          Atualizar
        </Button>
        <Button variant="ghost" size="icon-sm" aria-label="Alertas">
          <Bell className="size-4" />
        </Button>
      </div>
    </header>
  );
}
