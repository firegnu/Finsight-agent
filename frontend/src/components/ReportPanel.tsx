import type { AgentStatus, AnalysisReport } from "../types";

interface Props {
  report: AnalysisReport | null;
  status: AgentStatus;
}

export function ReportPanel({ report, status }: Props) {
  if (!report) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm">
        {status === "running" ? "🔍 正在生成报告..." : "📋 等待分析结果"}
      </div>
    );
  }
  return (
    <div className="h-full p-4 overflow-auto">
      <h2 className="text-sm font-semibold text-slate-700 mb-3">📊 分析报告</h2>
      <pre className="text-xs bg-slate-50 p-2 rounded">
        {JSON.stringify(report, null, 2)}
      </pre>
    </div>
  );
}
