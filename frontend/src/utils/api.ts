import type {
  ApprovalDecision,
  ApprovalRecord,
  CaseDetail,
  CasesResponse,
  HealthResponse,
  KPIResponse,
  SkillDetail,
  SkillsResponse,
  TraceDetail,
  TracesListResponse,
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

export async function fetchApproval(reportId: string): Promise<ApprovalRecord> {
  const resp = await fetch(`/api/approve/${encodeURIComponent(reportId)}`);
  if (!resp.ok) throw new Error(`Approval fetch failed: ${resp.status}`);
  return resp.json();
}

export async function submitApproval(
  reportId: string,
  decision: ApprovalDecision,
  extras?: { trace_id?: string; decided_by?: string; note?: string },
): Promise<ApprovalRecord> {
  const resp = await fetch(`/api/approve/${encodeURIComponent(reportId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, ...extras }),
  });
  if (!resp.ok) throw new Error(`Approval submit failed: ${resp.status}`);
  return resp.json();
}

export async function revokeApproval(reportId: string): Promise<void> {
  const resp = await fetch(`/api/approve/${encodeURIComponent(reportId)}`, {
    method: "DELETE",
  });
  if (!resp.ok) throw new Error(`Approval revoke failed: ${resp.status}`);
}

export async function fetchTraces(limit = 50): Promise<TracesListResponse> {
  const resp = await fetch(`/api/traces?limit=${limit}`);
  if (!resp.ok) throw new Error(`Traces fetch failed: ${resp.status}`);
  return resp.json();
}

export async function fetchTraceDetail(id: string): Promise<TraceDetail> {
  const resp = await fetch(`/api/traces/${encodeURIComponent(id)}`);
  if (!resp.ok) throw new Error(`Trace fetch failed: ${resp.status}`);
  return resp.json();
}

export async function deleteTrace(id: string): Promise<void> {
  const resp = await fetch(`/api/traces/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  if (!resp.ok) throw new Error(`Trace delete failed: ${resp.status}`);
}

export async function fetchSkills(): Promise<SkillsResponse> {
  const resp = await fetch("/api/skills");
  if (!resp.ok) throw new Error(`Skills fetch failed: ${resp.status}`);
  return resp.json();
}

export async function fetchSkillDetail(name: string): Promise<SkillDetail> {
  const resp = await fetch(`/api/skills/${encodeURIComponent(name)}`);
  if (!resp.ok) throw new Error(`Skill fetch failed: ${resp.status}`);
  return resp.json();
}
