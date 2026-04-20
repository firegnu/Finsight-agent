import { useEffect, useState } from "react";
import type { ApprovalDecision, ApprovalRecord } from "../types";
import {
  fetchApproval,
  revokeApproval,
  submitApproval,
} from "../utils/api";

interface Props {
  reportId: string;
  traceId?: string;
  requiresReview: boolean;
}

type SubmitState = "idle" | "submitting" | "error";

export function ApprovalButtons({ reportId, traceId, requiresReview }: Props) {
  const [record, setRecord] = useState<ApprovalRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitState, setSubmitState] = useState<SubmitState>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchApproval(reportId)
      .then((r) => !cancelled && setRecord(r))
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [reportId]);

  const submit = async (decision: ApprovalDecision) => {
    setSubmitState("submitting");
    setError(null);
    try {
      const updated = await submitApproval(reportId, decision, {
        trace_id: traceId,
      });
      setRecord(updated);
      setSubmitState("idle");
    } catch (e) {
      setError((e as Error).message);
      setSubmitState("error");
    }
  };

  const revoke = async () => {
    setSubmitState("submitting");
    setError(null);
    try {
      await revokeApproval(reportId);
      setRecord({
        report_id: reportId,
        trace_id: traceId ?? null,
        decision: null,
        decided_by: null,
        note: null,
      });
      setSubmitState("idle");
    } catch (e) {
      setError((e as Error).message);
      setSubmitState("error");
    }
  };

  if (!requiresReview) {
    return (
      <div className="text-xs text-ink-500 font-serif italic">
        ✓ 此报告无需人工审批
      </div>
    );
  }
  if (loading) {
    return <div className="text-xs text-ink-400 italic">加载审批状态…</div>;
  }

  const decision = record?.decision ?? null;
  const disabled = submitState === "submitting";

  if (decision === "approved") {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm font-serif font-bold text-emerald-800">
          <span>✓ 已批准执行</span>
          {record?.decided_at && (
            <span className="text-[10px] text-ink-400 font-mono font-normal">
              {formatTime(record.decided_at)}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={revoke}
          disabled={disabled}
          className="text-xs text-ink-500 hover:text-ink-800 underline underline-offset-2 disabled:opacity-50"
        >
          撤销
        </button>
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    );
  }

  if (decision === "rejected") {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm font-serif font-bold text-seal">
          <span>✗ 已驳回</span>
          {record?.decided_at && (
            <span className="text-[10px] text-ink-400 font-mono font-normal">
              {formatTime(record.decided_at)}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={revoke}
          disabled={disabled}
          className="text-xs text-ink-500 hover:text-ink-800 underline underline-offset-2 disabled:opacity-50"
        >
          撤销
        </button>
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => submit("approved")}
        disabled={disabled}
        className="px-4 py-1.5 text-sm rounded-sm bg-emerald-700 text-paper-50 hover:bg-emerald-800 font-medium tracking-wide transition-colors disabled:bg-ink-300 disabled:cursor-wait"
      >
        {submitState === "submitting" ? "提交中…" : "✓ 批准执行"}
      </button>
      <button
        type="button"
        onClick={() => submit("rejected")}
        disabled={disabled}
        className="px-4 py-1.5 text-sm rounded-sm bg-seal-50 text-seal border border-seal/40 hover:bg-seal-100 hover:border-seal font-medium tracking-wide transition-colors disabled:opacity-50"
      >
        ✗ 驳回
      </button>
      <span className="text-[11px] text-ink-400 ml-2 font-serif italic">
        审批决策会持久化到 SQLite
      </span>
      {error && (
        <span className="text-xs text-red-600 ml-2">⚠️ {error}</span>
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
    });
  } catch {
    return iso;
  }
}
