import type { AgentStatus, AnalysisReport } from "../types";
import { ActionItemCard } from "./ActionItemCard";
import { AnomalyCard } from "./AnomalyCard";
import { ApprovalButtons } from "./ApprovalButtons";

interface Props {
  report: AnalysisReport | null;
  status: AgentStatus;
}

export function ReportPanel({ report, status }: Props) {
  if (!report) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400 text-sm">
        {status === "running" ? (
          <span className="inline-flex items-center gap-2">
            <span className="inline-block w-3 h-3 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
            正在生成报告...
          </span>
        ) : status === "error" ? (
          <span>❌ 分析失败，请查看左侧错误信息</span>
        ) : (
          <span>📋 等待分析结果</span>
        )}
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-none px-4 py-3 border-b border-slate-200 bg-white flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-700">📊 分析报告</h2>
          <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
            期间 {report.period} · {report.report_id} · {formatTime(report.generated_at)}
          </div>
        </div>
        {report.requires_human_review && (
          <span className="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-700 font-medium">
            需人工审批
          </span>
        )}
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-5">
        <Section title="执行摘要">
          <p className="text-sm text-slate-800 leading-relaxed bg-blue-50 border-l-4 border-blue-400 p-3 rounded-r">
            {report.executive_summary}
          </p>
        </Section>

        {report.key_findings.length > 0 && (
          <Section title={`关键发现 (${report.key_findings.length})`}>
            <ul className="text-sm text-slate-700 space-y-1.5">
              {report.key_findings.map((f, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-slate-400 shrink-0">•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {report.anomalies.length > 0 && (
          <Section title={`异常项 (${report.anomalies.length})`}>
            <div className="space-y-2">
              {report.anomalies.map((a, i) => (
                <AnomalyCard key={i} anomaly={a} />
              ))}
            </div>
          </Section>
        )}

        {report.action_items.length > 0 && (
          <Section title={`行动建议 (${report.action_items.length})`}>
            <div className="space-y-2">
              {report.action_items.map((a, i) => (
                <ActionItemCard key={i} item={a} />
              ))}
            </div>
          </Section>
        )}

        {report.data_sources.length > 0 && (
          <div className="text-[11px] text-slate-500 pt-2 border-t border-slate-100">
            <span className="font-semibold">数据来源：</span>
            {report.data_sources.join(" · ")}
          </div>
        )}
      </div>

      <div className="flex-none px-4 py-3 border-t border-slate-200 bg-slate-50">
        <ApprovalButtons
          reportId={report.report_id}
          requiresReview={report.requires_human_review}
        />
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="text-[11px] uppercase tracking-wider text-slate-500 font-bold mb-2">
        {title}
      </h3>
      {children}
    </section>
  );
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}
