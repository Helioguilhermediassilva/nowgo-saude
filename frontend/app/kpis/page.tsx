import { KpiCards } from "@/components/dashboard/kpi-cards";
import { getKpis } from "@/lib/dashboard-server";

export const dynamic = "force-dynamic";

export default async function KpisIndexPage() {
  const items = await getKpis();
  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <KpiCards items={items} />
    </main>
  );
}
