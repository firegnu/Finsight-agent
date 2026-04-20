import type { AgentStatus, AnalysisReport, CaseMeta } from "../types";
import { ActionItemCard } from "./ActionItemCard";
import { AnomalyCard } from "./AnomalyCard";
import { ApprovalButtons } from "./ApprovalButtons";

interface Props {
  report: AnalysisReport | null;
  status: AgentStatus;
  casesById: Record<string, CaseMeta>;
  onOpenCase: (id: string) => void;
  onOpenTrace?: (traceId: string) => void;
}

export function ReportPanel({
  report,
  status,
  casesById,
  onOpenCase,
  onOpenTrace,
}: Props) {
  if (!report) {
    return (
      <div className="h-full flex items-center justify-center text-ink-400 text-sm px-6 text-center italic">
        {status === "running" ? (
          <span className="inline-flex items-center gap-2">
            <span className="inline-block w-3 h-3 border-2 border-ink-200 border-t-seal rounded-full animate-spin" />
            正在生成报告…
          </span>
        ) : status === "error" ? (
          <span>❌ 分析失败，请查看左侧错误信息</span>
        ) : status === "done" ? (
          <span>💬 此次为对话式回复，未生成结构化报告</span>
        ) : (
          <span>📋 等待分析结果</span>
        )}
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex-none px-5 py-3 border-b border-ink-200 bg-paper-50 flex items-center justify-between">
        <div>
          <h2 className="font-serif text-base font-bold text-ink-900 tracking-tight flex items-baseline gap-2">
            分析报告
            <span className="font-serif italic font-normal text-ink-500 text-sm">
              / Analysis
            </span>
          </h2>
          <div className="text-[11px] text-ink-500 mt-1 font-mono flex items-center gap-2 flex-wrap">
            <span>{report.period}</span>
            <span className="text-ink-300">·</span>
            <span>{report.report_id}</span>
            <span className="text-ink-300">·</span>
            <span>{formatTime(report.generated_at)}</span>
            {onOpenTrace && (
              <>
                <span className="text-ink-300">·</span>
                <button
                  type="button"
                  onClick={() => onOpenTrace(report.trace_id)}
                  className="text-seal hover:text-seal-600 underline underline-offset-2 decoration-seal/40"
                  title="查看完整推理 trace"
                >
                  查看 trace
                </button>
              </>
            )}
          </div>
        </div>
        {report.requires_human_review && (
          <span className="text-xs px-2 py-0.5 rounded-sm border border-orange-300/70 bg-orange-50/70 text-orange-800 font-medium">
            需人工审批
          </span>
        )}
      </div>

      <div className="flex-1 overflow-auto px-5 py-5 space-y-6">
        <Section title="执行摘要" subtitle="Executive Summary">
          <p className="font-serif text-[15px] text-ink-800 leading-relaxed first-letter:font-serif first-letter:text-3xl first-letter:font-bold first-letter:text-seal first-letter:pr-1.5 first-letter:float-left first-letter:leading-[1.1]">
            {report.executive_summary}
          </p>
        </Section>

        {report.key_findings.length > 0 && (
          <Section
            title={`关键发现 (${report.key_findings.length})`}
            subtitle="Key Findings"
          >
            <ul className="text-sm text-ink-800 space-y-2">
              {report.key_findings.map((f, i) => (
                <li key={i} className="flex gap-3 leading-relaxed">
                  <span className="font-mono text-seal shrink-0 mt-0.5">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {report.anomalies.length > 0 && (
          <Section
            title={`异常项 (${report.anomalies.length})`}
            subtitle="Anomalies"
          >
            <div className="space-y-2">
              {report.anomalies.map((a, i) => (
                <AnomalyCard
                  key={i}
                  anomaly={a}
                  casesById={casesById}
                  onOpenCase={onOpenCase}
                />
              ))}
            </div>
          </Section>
        )}

        {report.action_items.length > 0 && (
          <Section
            title={`行动建议 (${report.action_items.length})`}
            subtitle="Action Items"
          >
            <div className="space-y-2">
              {report.action_items.map((a, i) => (
                <ActionItemCard key={i} item={a} />
              ))}
            </div>
          </Section>
        )}

        {report.data_sources.length > 0 && (
          <div className="text-[11px] text-ink-500 pt-3 border-t border-ink-200 flex items-baseline gap-2 flex-wrap">
            <span className="font-serif italic text-ink-600">数据来源</span>
            <span className="font-mono">
              {report.data_sources.join(" · ")}
            </span>
          </div>
        )}
      </div>

      <div className="flex-none px-5 py-3 border-t border-ink-200 bg-paper-100">
        <ApprovalButtons
          reportId={report.report_id}
          traceId={report.trace_id}
          requiresReview={report.requires_human_review}
        />
      </div>
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3 className="flex items-baseline gap-2 mb-3 pb-1.5 border-b border-ink-200">
        <span className="font-serif text-sm font-bold text-ink-900 tracking-tight">
          {title}
        </span>
        {subtitle && (
          <span className="font-serif italic text-[11px] text-ink-500">
            {subtitle}
          </span>
        )}
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
