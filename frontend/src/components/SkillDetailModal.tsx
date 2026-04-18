import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { SkillDetail } from "../types";
import { fetchSkillDetail } from "../utils/api";

interface Props {
  name: string | null;
  onClose: () => void;
}

export function SkillDetailModal({ name, onClose }: Props) {
  const [detail, setDetail] = useState<SkillDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) {
      setDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchSkillDetail(name)
      .then(setDetail)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [name]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (name) document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [name, onClose]);

  if (!name) return null;

  return (
    <div
      className="fixed inset-0 bg-slate-900/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-none px-5 py-3 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">🎯</span>
            <div>
              <div className="text-xs text-slate-400 font-mono">
                skill · {detail?.category ?? "…"}
              </div>
              <h2 className="text-sm font-semibold text-slate-800">{name}</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 text-lg leading-none px-2"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4">
          {loading && <div className="text-sm text-slate-400">加载中...</div>}
          {error && (
            <div className="text-sm text-red-600 bg-red-50 rounded p-2">
              ⚠️ {error}
            </div>
          )}
          {detail && (
            <>
              <div className="mb-3 p-2 bg-indigo-50/50 border border-indigo-100 rounded text-[13px] text-indigo-900">
                {detail.description}
              </div>
              <div className="flex flex-wrap gap-1.5 mb-3">
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                  分类：{detail.category}
                </span>
                {detail.applicable_metrics.length > 0 && (
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-100 font-mono">
                    适用指标：{detail.applicable_metrics.join(", ")}
                  </span>
                )}
              </div>
              <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-headings:text-slate-800 prose-p:text-slate-700 prose-li:text-slate-700 prose-code:text-pink-600 prose-code:bg-pink-50 prose-code:px-1 prose-code:rounded prose-table:text-sm">
                <ReactMarkdown>{detail.content}</ReactMarkdown>
              </div>
            </>
          )}
        </div>
        <div className="flex-none px-5 py-2 border-t border-slate-100 text-[11px] text-slate-400">
          Esc 关闭 · {detail?.source_file}
        </div>
      </div>
    </div>
  );
}
