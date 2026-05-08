// Server-side data accessors used by the dashboard page during SSR.
// Calls into the same mock module the API routes use, avoiding an
// extra network hop while keeping the seam in place for the future
// when these become real backend calls.

export {
  getAlerts,
  getAttentionUnits,
  getHeatmap,
  getKpis,
  getPipelineHealth,
  getTimeSeries,
  getTopics,
} from "./mock-data";
