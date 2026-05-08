import { AlertOctagon, Activity } from "lucide-react";
import type { PipelineHealth } from "@/lib/types";

export function DegradationBanner({ health }: { health: PipelineHealth }) {
  if (health.status === "ok") return null;
  const isDown = health.status === "down";
  return (
    <div
      role="status"
      className={
        "flex items-start gap-3 border-b px-4 py-2.5 text-sm lg:px-6 " +
        (isDown
          ? "border-destructive/40 bg-destructive/10 text-destructive"
          : "border-yellow-500/40 bg-yellow-500/10 text-yellow-900 dark:text-yellow-200")
      }
    >
      {isDown ? (
        <AlertOctagon className="mt-0.5 size-4 shrink-0" />
      ) : (
        <Activity className="mt-0.5 size-4 shrink-0" />
      )}
      <div className="flex flex-col">
        <span className="font-medium">
          {isDown
            ? "Pipeline indisponível"
            : "Pipeline em modo degradado — dados podem estar atrasados"}
        </span>
        <span className="text-xs opacity-80">
          Latência p95 {health.latencyP95Seconds}s · limite {health.thresholdSeconds}s ·
          última ingestão{" "}
          {new Date(health.lastSuccessfulIngestionAt).toLocaleTimeString("pt-BR")}
        </span>
      </div>
    </div>
  );
}
