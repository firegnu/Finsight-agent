import { useEffect, useRef } from "react";
import type { AgentStatus, SSEEvent } from "../types";

interface Props {
  events: SSEEvent[];
  status: AgentStatus;
  error: string | null;
}

export function ReasoningPanel({ events, status, error }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [events.length, status]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex-none px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-white">
        <h2 className="text-sm font-semibold text-slate-700">🧠 Agent 推理过程</h2>
        <StatusPill status={status} />
      </div>
      <div ref={scrollRef} className="flex-1 overflow-auto p-4 space-y-2">
        {events.length === 0 && !error && status === "idle" && (
          <div className="text-sm text-slate-400 italic">
            等待输入分析需求...
          </div>
        )}
        {events.map((e, i) => (
          <EventItem key={i} event={e} />
        ))}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-2">
            ⚠️ {error}
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: AgentStatus }) {
  const cfg: Record<AgentStatus, { label: string; cls: string }> = {
    idle: { label: "就绪", cls: "bg-slate-100 text-slate-600" },
    running: { label: "● 运行中", cls: "bg-blue-100 text-blue-700 animate-pulse" },
    done: { label: "✓ 完成", cls: "bg-green-100 text-green-700" },
    error: { label: "✗ 错误", cls: "bg-red-100 text-red-700" },
  };
  const c = cfg[status];
  return <span className={`text-xs px-2 py-0.5 rounded font-medium ${c.cls}`}>{c.label}</span>;
}

function asString(v: unknown, fallback = ""): string {
  return typeof v === "string" ? v : fallback;
}

function EventItem({ event }: { event: SSEEvent }) {
  const { type, data } = event;
  switch (type) {
    case "start":
      return (
        <div className="text-xs text-slate-500 border-l-2 border-slate-200 pl-2 py-0.5">
          🚀 开始分析:{" "}
          <span className="font-medium text-slate-700">
            {asString(data.query)}
          </span>
        </div>
      );
    case "thinking":
      return (
        <div className="text-sm text-slate-600 italic border-l-2 border-indigo-300 pl-3 py-1 bg-indigo-50/40 rounded-r whitespace-pre-wrap">
          💭 {asString(data.content)}
        </div>
      );
    case "tool_call":
      return (
        <div className="text-sm bg-blue-50 border border-blue-200 rounded p-2">
          <div>
            🔧 调用工具{" "}
            <span className="font-mono font-semibold text-blue-800">
              {asString(data.name)}
            </span>
          </div>
          <pre className="text-xs text-slate-600 mt-1 whitespace-pre-wrap break-all font-mono">
            {JSON.stringify(data.args, null, 2)}
          </pre>
        </div>
      );
    case "tool_result":
      return (
        <div className="text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 rounded p-2">
          <span className="font-mono text-xs text-emerald-600 mr-2">
            {asString(data.name)}
          </span>
          {asString(data.summary)}
        </div>
      );
    case "tool_error":
      return (
        <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
          ❌ <span className="font-mono">{asString(data.name)}</span> 失败:{" "}
          {asString(data.error)}
        </div>
      );
    case "final_text":
      return (
        <div className="text-sm text-slate-800 bg-slate-100 rounded p-2 whitespace-pre-wrap">
          {asString(data.content)}
        </div>
      );
    case "report":
      return (
        <div className="text-xs text-emerald-600 border-l-2 border-emerald-400 pl-2 py-0.5">
          📝 报告已生成，见右侧面板
        </div>
      );
    case "done": {
      const latency =
        typeof data.total_latency_ms === "number" ? data.total_latency_ms : 0;
      return (
        <div className="text-xs text-slate-400 pt-1 border-t border-slate-100">
          ✓ 完成 · 总耗时 {(latency / 1000).toFixed(1)}s
        </div>
      );
    }
    case "error":
      return null;
    default:
      return null;
  }
}
