import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
  vi.restoreAllMocks();
  vi.resetModules();
});

beforeEach(() => {
  vi.resetModules();
});

describe("dashboard-server.getPipelineHealth", () => {
  it("falls back to mock when BACKEND_API_URL is not configured", async () => {
    delete process.env.BACKEND_API_URL;
    const { getPipelineHealth } = await import("@/lib/dashboard-server");
    const health = await getPipelineHealth();
    expect(health.status).toBe("ok");
    expect(health.thresholdSeconds).toBeGreaterThan(0);
  });

  it("bridges /health + /api/v1/metrics when backend is configured and healthy", async () => {
    process.env.BACKEND_API_URL = "https://backend.example.test";
    process.env.BACKEND_API_TOKEN = "t-secret";

    const updatedAt = new Date().toISOString();
    const fetchMock = vi.fn(async (url: string | URL) => {
      const u = typeof url === "string" ? url : url.toString();
      if (u.endsWith("/health")) {
        return new Response(JSON.stringify({ status: "ok", environment: "prod" }), { status: 200 });
      }
      if (u.endsWith("/api/v1/metrics")) {
        return new Response(
          JSON.stringify({
            events_per_minute: 12,
            p95_latency_ms: 80_000,
            dlq_depth: 0,
            anonymization_failures_24h: 0,
            updated_at: updatedAt,
          }),
          { status: 200 },
        );
      }
      return new Response("not found", { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const { getPipelineHealth } = await import("@/lib/dashboard-server");
    const health = await getPipelineHealth();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(health.status).toBe("ok");
    expect(health.latencyP95Seconds).toBe(80);
    expect(health.lastSuccessfulIngestionAt).toBe(updatedAt);
  });

  it("flags degraded when p95 latency crosses the threshold", async () => {
    process.env.BACKEND_API_URL = "https://backend.example.test";
    process.env.BACKEND_API_TOKEN = "t-secret";

    const fetchMock = vi.fn(async (url: string | URL) => {
      const u = typeof url === "string" ? url : url.toString();
      if (u.endsWith("/health")) {
        return new Response(JSON.stringify({ status: "ok", environment: "prod" }), { status: 200 });
      }
      return new Response(
        JSON.stringify({
          events_per_minute: 0,
          p95_latency_ms: 600_000,
          dlq_depth: 0,
          anonymization_failures_24h: 0,
          updated_at: new Date().toISOString(),
        }),
        { status: 200 },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { getPipelineHealth } = await import("@/lib/dashboard-server");
    const health = await getPipelineHealth();
    expect(health.status).toBe("degraded");
    expect(health.message).toContain("threshold");
  });

  it("falls back to mock when /health request fails", async () => {
    process.env.BACKEND_API_URL = "https://backend.example.test";
    const fetchMock = vi.fn(async () => new Response("oops", { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);

    const { getPipelineHealth } = await import("@/lib/dashboard-server");
    const health = await getPipelineHealth();
    expect(health.status).toBe("ok");
    expect(health.thresholdSeconds).toBeGreaterThan(0);
  });
});
