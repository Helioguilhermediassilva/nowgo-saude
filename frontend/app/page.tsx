import { AlertsPanel } from "@/components/dashboard/alerts-panel";
import { AttentionList } from "@/components/dashboard/attention-list";
import { HeatmapRegions } from "@/components/dashboard/heatmap-regions";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { TimeSeriesChart } from "@/components/dashboard/timeseries-chart";
import { TopicsChart } from "@/components/dashboard/topics-chart";
import {
  getAlerts,
  getAttentionUnits,
  getHeatmap,
  getKpis,
  getTimeSeries,
  getTopics,
} from "@/lib/dashboard-server";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [kpis, heatmap, attention, timeseries, topics, alerts] = await Promise.all([
    getKpis(),
    getHeatmap(),
    getAttentionUnits(),
    getTimeSeries(24),
    getTopics(),
    getAlerts(),
  ]);

  return (
    <main className="flex flex-1 flex-col gap-4 p-4 lg:p-6">
      <KpiCards items={kpis} />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <TimeSeriesChart items={timeseries} />
        </div>
        <TopicsChart items={topics} />
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <HeatmapRegions items={heatmap} />
        <div className="xl:col-span-2">
          <AttentionList items={attention} />
        </div>
      </div>
      <AlertsPanel items={alerts} />
    </main>
  );
}
