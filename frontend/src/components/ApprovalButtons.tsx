import { useEffect, useState } from "react";

interface Props {
  reportId: string;
  requiresReview: boolean;
}

type Decision = "pending" | "approved" | "rejected";

// Local-only approval state for demo. Week 2 will POST to /api/approve/{report_id}
// and persist decisions in SQLite.
export function ApprovalButtons({ reportId, requiresReview }: Props) {
  const [decision, setDecision] = useState<Decision>("pending");

  // Reset when report changes.
  useEffect(() => {
    setDecision("pending");
  }, [reportId]);

  if (!requiresReview) {
    return <div className="text-xs text-slate-500">✓ 此报告无需人工审批</div>;
  }

  if (decision === "approved") {
    return (
      <div className="flex items-center gap-2 text-sm font-semibold text-green-700">
        <span>✓ 已批准执行</span>
        <button
          type="button"
          onClick={() => setDecision("pending")}
          className="text-xs text-slate-400 hover:text-slate-600 underline"
        >
          撤销
        </button>
      </div>
    );
  }

  if (decision === "rejected") {
    return (
      <div className="flex items-center gap-2 text-sm font-semibold text-red-700">
        <span>✗ 已驳回</span>
        <button
          type="button"
          onClick={() => setDecision("pending")}
          className="text-xs text-slate-400 hover:text-slate-600 underline"
        >
          撤销
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => setDecision("approved")}
        className="px-4 py-1.5 text-sm rounded bg-green-600 text-white hover:bg-green-700 font-medium transition-colors"
      >
        ✓ 批准执行
      </button>
      <button
        type="button"
        onClick={() => setDecision("rejected")}
        className="px-4 py-1.5 text-sm rounded bg-red-100 text-red-700 hover:bg-red-200 font-medium transition-colors"
      >
        ✗ 驳回
      </button>
      <span className="text-[11px] text-slate-400 ml-2">
        (week 2 接入真实审批 API)
      </span>
    </div>
  );
}
