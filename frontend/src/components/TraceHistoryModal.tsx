import { useEffect, useState } from "react";
import type {
  TraceDetail,
  TraceStepRecord,
  TraceSummary,
} from "../types";
import { deleteTrace, fetchTraceDetail, fetchTraces } from "../utils/api";

interface Props {
  open: boolean;
  onClose: () => void;
  initialTraceId?: string | null;
  onReuseQuery?: (query: string) => void;
}

export function TraceHistoryModal({
  open,
  onClose,
  initialTraceId,
  onReuseQuery,
}: Props) {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TraceDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetchTraces(50);
      setTraces(r.traces);
      if (r.traces.length > 0 && !selectedId) {
        setSelectedId(r.traces[0].trace_id);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (open && initialTraceId) {
      setSelectedId(initialTraceId);
    }
  }, [open, initialTraceId]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    fetchTraceDetail(selectedId)
      .then((d) => !cancelled && setDetail(d))
      .catch((e: Error) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (open) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const onDelete = async (id: string) => {
    if (!confirm(`删除这条历史分析记录？\ntrace_id: ${id}`)) return;
    try {
      await deleteTrace(id);
      if (selectedId === id) setSelectedId(null);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-ink-900/60 backdrop-blur-[2px] flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-paper rounded-sm shadow-paper-lg border border-ink-300 w-full max-w-5xl h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-none px-5 py-3 border-b border-ink-200 bg-paper-50 flex items-center justify-between">
          <div className="flex items-baseline gap-3">
            <span className="text-lg">📋</span>
            <h2 className="font-serif text-lg font-bold text-ink-900 tracking-tight">
              历史分析
              <span className="font-serif italic font-normal text-ink-500 text-sm ml-2">
                / {traces.length} traces
              </span>
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-ink-400 hover:text-ink-900 text-xl leading-none px-2"
          >
            ×
          </button>
        </div>

        {error && (
          <div className="flex-none mx-5 my-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm p-2">
            ⚠️ {error}
          </div>
        )}

        <div className="flex-1 flex min-h-0">
          {/* Left: trace list */}
          <div className="w-[38%] border-r border-ink-200 overflow-auto bg-paper-50">
            {loading && (
              <div className="p-4 text-sm text-ink-400 italic">加载中…</div>
            )}
            {!loading && traces.length === 0 && (
              <div className="p-4 text-sm text-ink-400 italic font-serif">
                还没有历史分析记录。发起一次分析后会出现在这里。
              </div>
            )}
            <ul className="divide-y divide-ink-200">
              {traces.map((t) => (
                <li key={t.trace_id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(t.trace_id)}
                    className={`w-full text-left px-4 py-3 hover:bg-paper-100 transition-colors ${
                      selectedId === t.trace_id
                        ? "bg-seal-50/50 border-l-2 border-seal"
                        : "border-l-2 border-transparent"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-sm font-medium text-ink-900 line-clamp-2 leading-snug">
                        {t.user_query}
                      </div>
                      <StatusChip status={t.status} />
                    </div>
                    <div className="flex gap-3 text-[11px] text-ink-500 mt-1.5 font-mono">
                      <span>{formatTime(t.started_at)}</span>
                      <span>{(t.total_latency_ms / 1000).toFixed(1)}s</span>
                      <span>{t.step_count} steps</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Right: trace detail */}
          <div className="flex-1 overflow-auto bg-paper">
            {!detail && !selectedId && (
              <div className="p-8 text-sm text-ink-400 italic font-serif">
                ← 从左侧选择一条记录查看详情
              </div>
            )}
            {detail && (
              <div className="p-5 space-y-5">
                <div>
                  <div className="text-[10px] text-ink-500 font-mono uppercase tracking-widest mb-1">
                    {detail.trace_id} · {detail.llm_model}
                  </div>
                  <h3 className="font-serif text-lg font-bold text-ink-900 tracking-tight mb-2 leading-snug">
                    {detail.user_query}
                  </h3>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-ink-500 font-mono">
                    <span>⏰ {formatTime(detail.started_at)}</span>
                    <span>
                      ⌛ {(detail.total_latency_ms / 1000).toFixed(1)}s
                    </span>
                    <span>🧮 {detail.step_count} steps</span>
                    <StatusChip status={detail.status} />
                    <div className="ml-auto flex items-center gap-3">
                      {onReuseQuery && (
                        <button
                          type="button"
                          onClick={() => {
                            onReuseQuery(detail.user_query);
                            onClose();
                          }}
                          className="text-[11px] text-seal hover:text-seal-600 underline underline-offset-2"
                          title="把这条 query 回填到输入框，可以切换 provider 再问一次"
                        >
                          🔁 再问一次
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => onDelete(detail.trace_id)}
                        className="text-[11px] text-ink-500 hover:text-seal underline underline-offset-2"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>

                {/* Steps */}
                <section>
                  <h4 className="text-[10px] uppercase tracking-widest font-medium text-ink-600 mb-2 pb-1 border-b border-ink-200">
                    推理步骤 · {detail.steps.length}
                  </h4>
                  <div className="space-y-1.5">
                    {detail.steps.map((s, i) => (
                      <StepRow key={i} step={s} />
                    ))}
                  </div>
                </section>

                {/* Final report */}
                {detail.final_report && (
                  <section>
                    <h4 className="text-[10px] uppercase tracking-widest font-medium text-ink-600 mb-2 pb-1 border-b border-ink-200">
                      最终报告
                    </h4>
                    <div className="bg-paper-50 border border-ink-200 rounded-sm p-3 space-y-2">
                      <p className="font-serif text-sm text-ink-800 leading-relaxed">
                        {detail.final_report.executive_summary}
                      </p>
                      <div className="text-xs text-ink-600 flex flex-wrap gap-x-4 gap-y-1 pt-2 border-t border-ink-200 font-mono">
                        <span>
                          期间 <span className="ml-1">{detail.final_report.period}</span>
                        </span>
                        <span>
                          异常 <span className="ml-1">{detail.final_report.anomalies.length}</span>
                        </span>
                        <span>
                          建议 <span className="ml-1">{detail.final_report.action_items.length}</span>
                        </span>
                        {detail.final_report.requires_human_review && (
                          <span className="text-orange-700 font-semibold">
                            · 需人工审批
                          </span>
                        )}
                      </div>
                    </div>
                  </section>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex-none px-5 py-2 border-t border-ink-200 text-[11px] text-ink-500 bg-paper-50 font-mono">
          Esc 关闭 <span className="mx-2 text-ink-300">·</span> 最多显示最近 50 条
        </div>
      </div>
    </div>
  );
}

function StatusChip({ status }: { status: string | null }) {
  const cfg: Record<string, { label: string; cls: string }> = {
    success: {
      label: "✓",
      cls: "border-emerald-400/70 text-emerald-800 bg-emerald-50",
    },
    error: {
      label: "✗",
      cls: "border-seal/50 text-seal bg-seal-50",
    },
    running: {
      label: "●",
      cls: "border-ink-300 text-ink-700 bg-paper-50",
    },
  };
  const c =
    cfg[status || "unknown"] || {
      label: "?",
      cls: "border-ink-200 text-ink-400 bg-paper-50",
    };
  return (
    <span
      className={`text-[10px] px-1.5 py-0.5 rounded-sm border font-mono font-medium shrink-0 ${c.cls}`}
    >
      {c.label}
    </span>
  );
}

function StepRow({ step }: { step: TraceStepRecord }) {
  const isTool = step.action_type === "tool_call";
  const bg = isTool
    ? "bg-paper-50 border-ink-200"
    : "bg-paper border-ink-200";

  return (
    <div className={`border rounded-sm p-2 ${bg} text-xs`}>
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-ink-400 font-mono w-10 shrink-0">
          #{step.step_number}
        </span>
        <span className="text-[10px] uppercase tracking-widest text-ink-500 font-medium">
          {step.action_type}
        </span>
        {step.tool_name && (
          <span className="font-mono font-semibold text-seal">
            {step.tool_name}
          </span>
        )}
        {step.latency_ms > 0 && (
          <span className="text-[10px] text-ink-400 ml-auto font-mono">
            {step.latency_ms}ms
          </span>
        )}
      </div>
      {step.tool_input && (
        <pre className="text-[11px] text-ink-600 mt-1 whitespace-pre-wrap break-all font-mono bg-paper-100/70 p-1 rounded-sm">
          {JSON.stringify(step.tool_input, null, 0)}
        </pre>
      )}
      {step.tool_output_summary && (
        <div className="text-[11px] text-ink-700 mt-1 leading-relaxed">
          {step.tool_output_summary}
        </div>
      )}
    </div>
  );
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
}
