import { registerOTel } from "@vercel/otel";

const SERVICE_NAME = process.env.OTEL_SERVICE_NAME ?? "nowgo-saude-frontend";

export function register() {
  registerOTel({
    serviceName: SERVICE_NAME,
  });
}
