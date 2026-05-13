import { AttentionList } from "@/components/dashboard/attention-list";
import { getAttentionUnits } from "@/lib/dashboard-server";

export const dynamic = "force-dynamic";

export default async function UnitsIndexPage() {
  const items = await getAttentionUnits();
  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <AttentionList items={items} />
    </main>
  );
}
