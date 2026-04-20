import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { CaseDetail } from "../types";
import { fetchCaseDetail } from "../utils/api";

interface Props {
  caseId: string | null;
  onClose: () => void;
}

export function CaseDetailModal({ caseId, onClose }: Props) {
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    fetchCaseDetail(caseId)
      .then(setDetail)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [caseId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!caseId) return null;

  return (
    <div
      className="fixed inset-0 bg-ink-900/60 backdrop-blur-[2px] flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-paper rounded-sm shadow-paper-lg border border-ink-300 w-full max-w-3xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex-none px-5 py-3 border-b border-ink-200 flex items-center justify-between bg-paper-50">
          <div className="flex items-baseline gap-3">
            <span className="text-lg">📚</span>
            <div>
              <div className="text-[10px] text-ink-500 font-mono uppercase tracking-widest">
                case · {caseId}
              </div>
              {detail && (
                <h2 className="font-serif text-lg font-bold text-ink-900 tracking-tight mt-0.5">
                  {detail.title}
                </h2>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-ink-400 hover:text-ink-900 text-xl leading-none px-2"
            aria-label="关闭"
          >
            ×
          </button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4">
          {loading && (
            <div className="text-sm text-ink-400 italic">加载案例中…</div>
          )}
          {error && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm p-2">
              ⚠️ {error}
            </div>
          )}
          {detail && (
            <>
              <div className="flex flex-wrap gap-1.5 mb-4">
                {detail.tags.map((t) => (
                  <span
                    key={t}
                    className="text-[11px] px-2 py-0.5 rounded-sm bg-paper-50 text-ink-700 border border-ink-200"
                  >
                    {t}
                  </span>
                ))}
                {detail.region && (
                  <span className="text-[11px] px-2 py-0.5 rounded-sm bg-amber-50 text-amber-800 border border-amber-200/70">
                    区域 · {detail.region}
                  </span>
                )}
                {detail.metric && (
                  <span className="text-[11px] px-2 py-0.5 rounded-sm bg-emerald-50 text-emerald-800 border border-emerald-200/70 font-mono">
                    {detail.metric}
                  </span>
                )}
                {detail.period && (
                  <span className="text-[11px] px-2 py-0.5 rounded-sm bg-paper-100 text-ink-700 border border-ink-200 font-mono">
                    {detail.period}
                  </span>
                )}
              </div>
              <div className="prose prose-sm max-w-none prose-headings:font-serif prose-headings:font-bold prose-headings:text-ink-900 prose-headings:tracking-tight prose-p:text-ink-800 prose-p:leading-relaxed prose-li:text-ink-800 prose-strong:text-ink-900 prose-code:text-seal prose-code:bg-seal-50 prose-code:px-1 prose-code:rounded-sm prose-code:font-mono">
                <ReactMarkdown>{detail.content}</ReactMarkdown>
              </div>
            </>
          )}
        </div>

        <div className="flex-none px-5 py-2 border-t border-ink-200 text-[11px] text-ink-500 font-mono bg-paper-50">
          <span className="font-serif italic not-italic">Esc 关闭</span>
          <span className="mx-2 text-ink-300">·</span>
          源文件 {detail?.source_file ?? "…"}
        </div>
      </div>
    </div>
  );
}
