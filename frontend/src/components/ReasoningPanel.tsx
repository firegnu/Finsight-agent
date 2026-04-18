import type { AgentStatus, SSEEvent } from "../types";

interface Props {
  events: SSEEvent[];
  status: AgentStatus;
  error: string | null;
}

export function ReasoningPanel({ events, status, error }: Props) {
  return (
    <div className="h-full p-4 overflow-auto">
      <h2 className="text-sm font-semibold text-slate-700 mb-3">
        🧠 Agent 推理过程
      </h2>
      <div className="text-xs text-slate-400">
        status: {status} · events: {events.length}
      </div>
      {error && (
        <div className="text-red-500 text-sm mt-2 bg-red-50 border border-red-200 rounded p-2">
          {error}
        </div>
      )}
    </div>
  );
}
