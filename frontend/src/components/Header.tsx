import { useEffect, useState } from "react";
import type { HealthResponse } from "../types";
import { fetchHealth } from "../utils/api";

interface Props {
  caseCount?: number;
  onOpenHistory?: () => void;
}

export function Header({ caseCount = 0, onOpenHistory }: Props) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const modelLabel = health ? `${health.model} · ${health.provider}` : "loading…";

  return (
    <header className="flex items-center justify-between px-6 h-14 border-b border-slate-200 bg-white">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold">
          F
        </div>
        <h1 className="text-lg font-semibold text-slate-800">FinSight Agent</h1>
        <span className="text-xs text-slate-400 hidden sm:inline">
          金融数据智能分析
        </span>
      </div>
      <div className="flex items-center gap-4 text-xs text-slate-500">
        {onOpenHistory && (
          <button
            type="button"
            onClick={onOpenHistory}
            className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-slate-100 text-slate-600 transition-colors"
            title="查看历史分析记录"
          >
            <span>📋</span>
            <span className="font-medium">历史分析</span>
          </button>
        )}
        {caseCount > 0 && (
          <div
            className="flex items-center gap-1.5 px-2 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-100"
            title="RAG 案例库：向量检索支持根因推理"
          >
            <span>📚</span>
            <span className="font-medium">{caseCount} 个历史案例</span>
            <span className="text-indigo-400">·</span>
            <span className="font-mono text-[10px]">768d · cosine</span>
          </div>
        )}
        <div className="flex items-center gap-2 font-mono">
          <span
            className={`w-2 h-2 rounded-full ${health ? "bg-green-500" : "bg-slate-300"}`}
          />
          <span>Model: {modelLabel}</span>
        </div>
      </div>
    </header>
  );
}
