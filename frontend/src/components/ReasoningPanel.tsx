import { useEffect, useRef } from "react";
import type { AgentStatus, RagHit, SkillMeta, SSEEvent } from "../types";
import { WaitingIndicator } from "./WaitingIndicator";

interface Props {
  events: SSEEvent[];
  status: AgentStatus;
  error: string | null;
  lastEventAt: number;
  onOpenCase: (id: string) => void;
  onOpenSkill: (name: string) => void;
}

const TERMINAL_TYPES = new Set(["final_text", "report", "done", "error"]);

export function ReasoningPanel({
  events,
  status,
  error,
  lastEventAt,
  onOpenCase,
  onOpenSkill,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [events.length, status, lastEventAt]);

  const lastType = events.length ? events[events.length - 1].type : null;
  const showWaiting =
    status === "running" && (lastType === null || !TERMINAL_TYPES.has(lastType));
  const waitingStage = lastType === "tool_call" ? "tool" : "thinking";

  return (
    <div className="h-full flex flex-col">
      <div className="flex-none px-5 py-3 border-b border-ink-200 bg-paper-50 flex items-center justify-between">
        <h2 className="font-serif text-base font-bold text-ink-900 tracking-tight flex items-baseline gap-2">
          <span>推理过程</span>
          <span className="font-serif italic font-normal text-ink-500 text-sm">
            / Reasoning
          </span>
        </h2>
        <StatusPill status={status} />
      </div>
      <div ref={scrollRef} className="flex-1 overflow-auto px-5 py-4 space-y-2">
        {events.length === 0 && !error && status === "idle" && (
          <div className="text-sm text-ink-400 italic font-serif">
            等待输入分析需求…
          </div>
        )}
        {events.map((e, i) => (
          <EventItem
            key={i}
            event={e}
            onOpenCase={onOpenCase}
            onOpenSkill={onOpenSkill}
          />
        ))}
        {showWaiting && (
          <WaitingIndicator key={lastEventAt} stage={waitingStage} />
        )}
        {error && (
          <div className="text-sm text-red-800 bg-red-50 border border-red-200 rounded-sm p-2">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: AgentStatus }) {
  const cfg: Record<AgentStatus, { label: string; cls: string }> = {
    idle: {
      label: "idle",
      cls: "border-ink-300 text-ink-500 bg-paper-100",
    },
    running: {
      label: "● running",
      cls: "border-seal/50 text-seal bg-seal-50/60 animate-pulse",
    },
    done: {
      label: "✓ done",
      cls: "border-emerald-400/70 text-emerald-800 bg-emerald-50/60",
    },
    error: {
      label: "✗ error",
      cls: "border-red-400/70 text-red-800 bg-red-50/60",
    },
  };
  const c = cfg[status];
  return (
    <span
      className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-sm border ${c.cls}`}
    >
      {c.label}
    </span>
  );
}

function asString(v: unknown, fallback = ""): string {
  return typeof v === "string" ? v : fallback;
}

function EventItem({
  event,
  onOpenCase,
  onOpenSkill,
}: {
  event: SSEEvent;
  onOpenCase: (id: string) => void;
  onOpenSkill: (name: string) => void;
}) {
  const { type, data } = event;
  switch (type) {
    case "start":
      return (
        <div className="text-xs text-ink-600 border-l border-ink-300 pl-3 py-0.5 font-serif italic">
          🚀 开始分析：
          <span className="font-sans not-italic font-medium text-ink-900 ml-1">
            {asString(data.query)}
          </span>
        </div>
      );
    case "thinking":
      return (
        <div className="text-sm text-ink-700 font-serif italic border-l border-seal/50 pl-3 py-1 bg-seal-50/30 rounded-r-sm whitespace-pre-wrap leading-relaxed">
          💭 {asString(data.content)}
        </div>
      );
    case "tool_call":
      return (
        <div className="text-sm border border-ink-200 bg-paper-50 rounded-sm p-2">
          <div className="text-ink-700">
            <span className="text-[10px] uppercase tracking-widest text-ink-500 font-medium mr-2">
              CALL
            </span>
            <span className="font-mono font-medium text-ink-900">
              {asString(data.name)}
            </span>
          </div>
          <pre className="text-[11px] text-ink-600 mt-1 whitespace-pre-wrap break-all font-mono bg-paper-200/40 rounded-sm p-1.5">
            {JSON.stringify(data.args, null, 2)}
          </pre>
        </div>
      );
    case "tool_result": {
      const name = asString(data.name);
      const summary = asString(data.summary);
      if (name === "use_skill" && data.skill) {
        const skill = data.skill as Partial<SkillMeta>;
        return (
          <div className="text-sm border border-amber-300/60 bg-amber-50/50 rounded-sm p-2">
            <div className="text-[10px] uppercase tracking-widest text-amber-800 font-medium mb-1.5">
              🎯 已加载方法论 skill
            </div>
            <button
              type="button"
              onClick={() => skill.name && onOpenSkill(skill.name)}
              className="w-full text-left bg-paper-50 border border-amber-200/80 rounded-sm p-2 hover:border-amber-500 hover:shadow-paper transition-all group"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-serif font-bold text-ink-900 group-hover:text-amber-900">
                  {skill.name}
                </span>
                <span className="text-[10px] text-amber-700 font-mono uppercase tracking-wider">
                  {skill.category}
                </span>
              </div>
              {skill.description && (
                <div className="text-xs text-ink-600 mt-1 line-clamp-2 leading-relaxed">
                  {skill.description}
                </div>
              )}
            </button>
          </div>
        );
      }
      if (name === "rag_search" && Array.isArray(data.hits)) {
        const hits = data.hits as RagHit[];
        return (
          <div className="text-sm border border-ink-200 bg-paper-50 rounded-sm p-2 space-y-1.5">
            <div className="text-[10px] uppercase tracking-widest text-ink-600 font-medium">
              📚 RAG 检索返回 <span className="font-mono">{hits.length}</span> 个案例
            </div>
            {hits.map((h) => (
              <button
                key={h.id}
                type="button"
                onClick={() => onOpenCase(h.id)}
                className="w-full text-left bg-paper border border-ink-200 rounded-sm p-2 hover:border-seal hover:shadow-paper transition-all group"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-serif font-medium text-ink-900 text-sm group-hover:text-seal">
                    {h.title}
                  </span>
                  <span className="text-[10px] text-ink-500 font-mono whitespace-nowrap">
                    score {h.score.toFixed(2)}
                  </span>
                </div>
                {h.snippet && (
                  <div className="text-xs text-ink-600 mt-1 line-clamp-2 leading-relaxed">
                    {h.snippet}
                  </div>
                )}
              </button>
            ))}
          </div>
        );
      }
      return (
        <div className="text-sm text-emerald-900 bg-emerald-50/50 border border-emerald-300/60 rounded-sm p-2">
          <span className="font-mono text-[10px] uppercase tracking-widest text-emerald-700 mr-2">
            {name}
          </span>
          {summary}
        </div>
      );
    }
    case "tool_error":
      return (
        <div className="text-sm text-red-800 bg-red-50/60 border border-red-300/70 rounded-sm p-2">
          ❌ <span className="font-mono">{asString(data.name)}</span> 失败：
          {asString(data.error)}
        </div>
      );
    case "final_text":
      return (
        <div className="text-sm text-ink-800 bg-paper-200/50 border border-ink-200 rounded-sm p-3 whitespace-pre-wrap leading-relaxed font-serif">
          {asString(data.content)}
        </div>
      );
    case "report":
      return (
        <div className="text-xs text-emerald-800 border-l border-emerald-500 pl-3 py-0.5 font-serif italic">
          📝 报告已生成，见右侧面板
        </div>
      );
    case "done": {
      const latency =
        typeof data.total_latency_ms === "number" ? data.total_latency_ms : 0;
      return (
        <div className="text-[11px] text-ink-500 pt-2 border-t border-ink-200 font-mono flex items-baseline gap-2">
          <span className="font-serif italic text-ink-600 not-italic">完成</span>
          <span>·</span>
          <span>total {(latency / 1000).toFixed(1)}s</span>
        </div>
      );
    }
    case "error":
      return null;
    default:
      return null;
  }
}
