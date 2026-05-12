import { PlaceholderPage } from "@/components/dashboard/placeholder-page";

export const dynamic = "force-dynamic";

export default function PipelinesPage() {
  return (
    <PlaceholderPage
      title="Pipelines de ingestão"
      description="Visão dedicada de saúde dos coletores (OuvidorSUS, GrokX/X, e demais conectores). Será habilitada na Phase H, quando substituirmos o seed sintético pela ingestão real."
      upcoming={[
        "Status por conector (uptime, p95 de latência, DLQ depth).",
        "Histórico de execuções dos jobs de classificação e anonimização.",
        "Trilha de auditoria por evento, alinhada à Feature 001.",
      ]}
    />
  );
}
