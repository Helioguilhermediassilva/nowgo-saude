import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  Building2,
  Gauge,
  Home,
  Map,
  MessagesSquare,
} from "lucide-react";

const NAV = [
  { href: "/", label: "Painel", icon: Home, active: true },
  { href: "#", label: "Mapa operacional", icon: Map },
  { href: "#", label: "Unidades", icon: Building2 },
  { href: "#", label: "Alertas", icon: AlertTriangle },
  { href: "#", label: "Tópicos", icon: MessagesSquare },
  { href: "#", label: "Pipelines", icon: Activity },
  { href: "#", label: "KPIs Smart City", icon: Gauge },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r border-border bg-card lg:flex lg:flex-col">
      <div className="flex h-14 items-center gap-2 border-b border-border px-4">
        <div className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground">
          <Activity className="size-4" />
        </div>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold">NowGo Saúde</span>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Comando · DF
          </span>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 p-2">
        {NAV.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              data-active={item.active ? "" : undefined}
              className="flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground data-[active]:bg-muted data-[active]:text-foreground"
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3 text-[11px] text-muted-foreground">
        <p className="font-medium text-foreground">Versão MVP</p>
        <p>Smart City · ISO 37120</p>
      </div>
    </aside>
  );
}
