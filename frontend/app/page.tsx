import { AlertsPanel } from "@/components/dashboard/alerts-panel";
import { AttentionList } from "@/components/dashboard/attention-list";
import { DegradationBanner } from "@/components/dashboard/degradation-banner";
import { Header } from "@/components/dashboard/header";
import { HeatmapRegions } from "@/components/dashboard/heatmap-regions";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { Sidebar } from "@/components/dashboard/sidebar";
import { TimeSeriesChart } from "@/components/dashboard/timeseries-chart";
import { TopicsChart } from "@/components/dashboard/topics-chart";
import {
  getAlerts,
  getAttentionUnits,
  getHeatmap,
  getKpis,
  getPipelineHealth,
  getTimeSeries,
  getTopics,
} from "@/lib/dashboard-server";

export const dynamic = "force-dynamic";

export default async function Home() {
  const kpis = getKpis();
  const heatmap = getHeatmap();
  const attention = getAttentionUnits();
  const timeseries = getTimeSeries(24);
  const topics = getTopics();
  const alerts = getAlerts();
  const health = await getPipelineHealth();

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <DegradationBanner health={health} />
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
      </div>
    </div>
  );
}
