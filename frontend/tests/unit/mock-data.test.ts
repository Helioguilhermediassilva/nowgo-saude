import { describe, expect, it } from "vitest";

import {
  getAlerts,
  getAttentionUnits,
  getHeatmap,
  getKpis,
  getPipelineHealth,
  getTimeSeries,
  getTopics,
} from "@/lib/mock-data";

describe("mock-data", () => {
  it("returns at least one KPI per Smart City framework reference", () => {
    const kpis = getKpis();
    expect(kpis.length).toBeGreaterThanOrEqual(4);
    for (const k of kpis) {
      expect(k.framework).toMatch(/ISO 37120|ITU-T Y.4900|IMD Smart City/);
      expect(k.reference).toBeTruthy();
      expect(k.source).toBeTruthy();
    }
  });

  it("heatmap entries have bounded pressure scores", () => {
    const items = getHeatmap();
    expect(items.length).toBeGreaterThanOrEqual(8);
    for (const r of items) {
      expect(r.pressureScore).toBeGreaterThanOrEqual(0);
      expect(r.pressureScore).toBeLessThanOrEqual(100);
      expect(["up", "down", "stable"]).toContain(r.trend);
    }
  });

  it("attention units expose severity and rationale", () => {
    const items = getAttentionUnits();
    expect(items.length).toBeGreaterThan(0);
    for (const u of items) {
      expect(u.attentionScore).toBeGreaterThanOrEqual(70);
      expect(["medium", "high", "critical"]).toContain(u.severity);
      expect(u.reason.length).toBeGreaterThan(10);
    }
  });

  it("time series returns the requested number of points + 1", () => {
    expect(getTimeSeries(6)).toHaveLength(7);
    expect(getTimeSeries(24)).toHaveLength(25);
  });

  it("topic distribution percentages sum to ~100%", () => {
    const topics = getTopics();
    const sum = topics.reduce((s, t) => s + t.pct, 0);
    expect(sum).toBeGreaterThan(99);
    expect(sum).toBeLessThan(101);
  });

  it("alerts and pipeline health are well-formed", () => {
    const alerts = getAlerts();
    expect(alerts.length).toBeGreaterThan(0);
    for (const a of alerts) {
      expect(["open", "acknowledged", "resolved"]).toContain(a.status);
    }
    const health = getPipelineHealth();
    expect(["ok", "degraded", "down"]).toContain(health.status);
    expect(health.thresholdSeconds).toBeGreaterThan(0);
  });
});
