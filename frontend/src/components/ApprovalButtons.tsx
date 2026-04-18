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

// Talks to POST/GET/DELETE /api/approve/{report_id} for persistence.
// Decisions survive page refresh because they're stored in SQLite.
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
    return <div className="text-xs text-slate-500">✓ 此报告无需人工审批</div>;
  }
  if (loading) {
    return <div className="text-xs text-slate-400">加载审批状态...</div>;
  }

  const decision = record?.decision ?? null;
  const disabled = submitState === "submitting";

  if (decision === "approved") {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-green-700">
          <span>✓ 已批准执行</span>
          {record?.decided_at && (
            <span className="text-[10px] text-slate-400 font-mono">
              {formatTime(record.decided_at)}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={revoke}
          disabled={disabled}
          className="text-xs text-slate-400 hover:text-slate-600 underline disabled:opacity-50"
        >
          撤销
        </button>
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }

  if (decision === "rejected") {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-red-700">
          <span>✗ 已驳回</span>
          {record?.decided_at && (
            <span className="text-[10px] text-slate-400 font-mono">
              {formatTime(record.decided_at)}
            </span>
          )}
        </div>
        <button
          type="button"
          onClick={revoke}
          disabled={disabled}
          className="text-xs text-slate-400 hover:text-slate-600 underline disabled:opacity-50"
        >
          撤销
        </button>
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => submit("approved")}
        disabled={disabled}
        className="px-4 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 font-medium transition-colors disabled:bg-slate-400 disabled:cursor-wait"
      >
        {submitState === "submitting" ? "提交中..." : "✓ 批准执行"}
      </button>
      <button
        type="button"
        onClick={() => submit("rejected")}
        disabled={disabled}
        className="px-4 py-1.5 text-sm rounded bg-red-100 text-red-700 hover:bg-red-200 font-medium transition-colors disabled:opacity-50"
      >
        ✗ 驳回
      </button>
      <span className="text-[11px] text-slate-400 ml-2">
        审批决策会持久化到 SQLite
      </span>
      {error && (
        <span className="text-xs text-red-500 ml-2">⚠️ {error}</span>
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
