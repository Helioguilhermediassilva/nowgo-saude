import { TopicsChart } from "@/components/dashboard/topics-chart";
import { getTopics } from "@/lib/dashboard-server";

export const dynamic = "force-dynamic";

export default async function TopicsIndexPage() {
  const items = await getTopics();
  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <TopicsChart items={items} />
    </main>
  );
}
