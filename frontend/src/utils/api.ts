import type { HealthResponse, KPIResponse } from "../types";

export async function fetchKPI(): Promise<KPIResponse> {
  const resp = await fetch("/api/kpi");
  if (!resp.ok) throw new Error(`KPI fetch failed: ${resp.status}`);
  return resp.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const resp = await fetch("/api/health");
  if (!resp.ok) throw new Error(`Health fetch failed: ${resp.status}`);
  return resp.json();
}
