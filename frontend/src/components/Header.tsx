import type { ProviderInfo } from "../types";
import { ProviderSwitcher } from "./ProviderSwitcher";

interface Props {
  caseCount?: number;
  skillCount?: number;
  onOpenHistory?: () => void;
  providers: ProviderInfo[];
  selectedProviderId: string | null;
  onProviderChange: (id: string) => void;
  providerSwitcherDisabled?: boolean;
}

export function Header({
  caseCount = 0,
  skillCount = 0,
  onOpenHistory,
  providers,
  selectedProviderId,
  onProviderChange,
  providerSwitcherDisabled,
}: Props) {
  return (
    <header className="flex items-center justify-between px-6 h-14 border-b border-ink-200 bg-paper/70 backdrop-blur-sm">
      <div className="flex items-baseline gap-3">
        <div className="w-7 h-7 rounded-sm bg-seal flex items-center justify-center text-paper-50 font-serif font-bold text-sm leading-none">
          F
        </div>
        <h1 className="font-serif text-xl font-bold text-ink-900 tracking-tight leading-none">
          FinSight
        </h1>
        <span className="font-serif italic text-xs text-ink-500 hidden sm:inline border-l border-ink-300 pl-3">
          信用卡业务分析台
        </span>
      </div>
      <div className="flex items-center gap-3 text-xs">
        {onOpenHistory && (
          <button
            type="button"
            onClick={onOpenHistory}
            className="flex items-center gap-1.5 px-2 py-1 rounded-sm text-ink-600 hover:text-ink-900 hover:underline underline-offset-4 decoration-ink-300 transition-colors"
            title="查看历史分析记录"
          >
            <span>📋</span>
            <span className="font-medium">历史分析</span>
          </button>
        )}
        {skillCount > 0 && (
          <div
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-sm border border-amber-300/60 bg-amber-50/60 text-amber-800"
            title="Agent 方法论 skills：按名字加载 SOP 指引"
          >
            <span>🎯</span>
            <span className="font-mono">{skillCount}</span>
            <span className="text-amber-600">skills</span>
          </div>
        )}
        {caseCount > 0 && (
          <div
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-sm border border-ink-200 bg-paper-50 text-ink-700"
            title="RAG 案例库：向量检索支持根因推理"
          >
            <span>📚</span>
            <span className="font-mono">{caseCount}</span>
            <span className="text-ink-500">cases</span>
            <span className="text-ink-300">·</span>
            <span className="font-mono text-[10px] text-ink-500">1024d · cosine</span>
          </div>
        )}
        <ProviderSwitcher
          providers={providers}
          selectedId={selectedProviderId}
          onChange={onProviderChange}
          disabled={providerSwitcherDisabled}
        />
      </div>
    </header>
  );
}
