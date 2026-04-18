import type {
  CaseDetail,
  CasesResponse,
  HealthResponse,
  KPIResponse,
} from "../types";

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

export async function fetchCases(): Promise<CasesResponse> {
  const resp = await fetch("/api/cases");
  if (!resp.ok) throw new Error(`Cases fetch failed: ${resp.status}`);
  return resp.json();
}

export async function fetchCaseDetail(id: string): Promise<CaseDetail> {
  const resp = await fetch(`/api/cases/${encodeURIComponent(id)}`);
  if (!resp.ok) throw new Error(`Case fetch failed: ${resp.status}`);
  return resp.json();
}
