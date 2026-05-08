import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { KpiCards } from "@/components/dashboard/kpi-cards";
import { AttentionList } from "@/components/dashboard/attention-list";
import { DegradationBanner } from "@/components/dashboard/degradation-banner";
import { getAttentionUnits, getKpis, getPipelineHealth } from "@/lib/mock-data";

describe("KpiCards", () => {
  it("renders one card per KPI with framework badge", () => {
    const kpis = getKpis();
    render(<KpiCards items={kpis} />);
    for (const k of kpis) {
      expect(screen.getByText(k.name)).toBeInTheDocument();
    }
    expect(
      screen.getAllByText(/ISO 37120|IMD Smart City|ITU-T Y\.4900/).length,
    ).toBeGreaterThan(0);
  });
});

describe("AttentionList", () => {
  it("orders units by attention score descending", () => {
    const units = getAttentionUnits();
    render(<AttentionList items={units} />);
    const sorted = units.slice().sort((a, b) => b.attentionScore - a.attentionScore);
    expect(screen.getByText(sorted[0].name)).toBeInTheDocument();
  });
});

describe("DegradationBanner", () => {
  it("renders nothing when pipeline is ok", () => {
    const ok = { ...getPipelineHealth(), status: "ok" as const };
    const { container } = render(<DegradationBanner health={ok} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a warning when pipeline is degraded", () => {
    const degraded = {
      ...getPipelineHealth(),
      status: "degraded" as const,
      latencyP95Seconds: 420,
    };
    render(<DegradationBanner health={degraded} />);
    expect(screen.getByRole("status")).toHaveTextContent(/degradado/i);
  });
});
