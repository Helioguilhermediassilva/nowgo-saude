import { AlertsPanel } from "@/components/dashboard/alerts-panel";
import { getAlerts } from "@/lib/dashboard-server";

export const dynamic = "force-dynamic";

export default async function AlertsIndexPage() {
  const items = await getAlerts();
  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <AlertsPanel items={items} />
    </main>
  );
}
