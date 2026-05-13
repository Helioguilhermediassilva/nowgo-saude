import { Construction } from "lucide-react";

interface PlaceholderPageProps {
  title: string;
  description: string;
  // Optional checklist of upcoming items shown in the body.
  upcoming?: readonly string[];
}

export function PlaceholderPage({ title, description, upcoming }: PlaceholderPageProps) {
  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <section className="flex flex-col gap-3 rounded-xl border border-border bg-card p-6">
        <div className="flex items-center gap-2">
          <Construction className="size-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold">{title}</h2>
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
        {upcoming && upcoming.length > 0 ? (
          <ul className="mt-2 flex flex-col gap-1 text-xs text-muted-foreground">
            {upcoming.map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span aria-hidden="true">·</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </main>
  );
}
