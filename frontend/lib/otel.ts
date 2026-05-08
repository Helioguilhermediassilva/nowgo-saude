"use client";

import { trace, type Tracer } from "@opentelemetry/api";
import { ZoneContextManager } from "@opentelemetry/context-zone";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { DocumentLoadInstrumentation } from "@opentelemetry/instrumentation-document-load";
import { FetchInstrumentation } from "@opentelemetry/instrumentation-fetch";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { BatchSpanProcessor, WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from "@opentelemetry/semantic-conventions";

const SERVICE_NAME = process.env.NEXT_PUBLIC_OTEL_SERVICE_NAME ?? "nowgo-saude-frontend";
const SERVICE_VERSION = process.env.NEXT_PUBLIC_APP_VERSION ?? "0.1.0";
const OTLP_ENDPOINT =
  process.env.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT ?? "http://localhost:4318/v1/traces";

let provider: WebTracerProvider | null = null;

export function initBrowserOTel(): Tracer {
  if (typeof window === "undefined") {
    return trace.getTracer(SERVICE_NAME);
  }
  if (provider) {
    return trace.getTracer(SERVICE_NAME);
  }

  provider = new WebTracerProvider({
    resource: resourceFromAttributes({
      [ATTR_SERVICE_NAME]: SERVICE_NAME,
      [ATTR_SERVICE_VERSION]: SERVICE_VERSION,
    }),
    spanProcessors: [new BatchSpanProcessor(new OTLPTraceExporter({ url: OTLP_ENDPOINT }))],
  });

  provider.register({
    contextManager: new ZoneContextManager(),
  });

  registerInstrumentations({
    instrumentations: [
      new DocumentLoadInstrumentation(),
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: [/.*/],
      }),
    ],
  });

  return trace.getTracer(SERVICE_NAME);
}

export function getTracer(): Tracer {
  return trace.getTracer(SERVICE_NAME);
}
