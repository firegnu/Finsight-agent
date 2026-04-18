import type { AnomalyFinding, CaseMeta, Severity } from "../types";

const SEVERITY_STYLE: Record<Severity, string> = {
  critical: "bg-red-100 border-red-400 text-red-900",
  high: "bg-orange-100 border-orange-400 text-orange-900",
  medium: "bg-yellow-100 border-yellow-400 text-yellow-900",
  low: "bg-blue-100 border-blue-400 text-blue-900",
};

const SEVERITY_EMOJI: Record<Severity, string> = {
  critical: "🔴",
  high: "🟠",
  medium: "🟡",
  low: "🔵",
};

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: "严重",
  high: "高",
  medium: "中",
  low: "低",
};

// Backend metric ids → 中文业务名（对齐 backend/agent/prompts.py FIELD_METADATA）.
const METRIC_LABEL: Record<string, string> = {
  overdue_rate: "逾期率",
  activation_rate: "激活率",
  churn_rate: "流失率",
  collection_recovery_rate: "催收回收率",
  new_customers: "新客获客量",
  revenue_per_customer: "客均收入",
  monthly_transaction_volume: "月交易额",
  customer_complaints: "客户投诉量",
};

function formatValue(metric: string, value: number): string {
  if (metric.endsWith("_rate")) return `${(value * 100).toFixed(2)}%`;
  if (metric === "new_customers" || metric === "customer_complaints") {
    return value.toLocaleString();
  }
  if (metric === "revenue_per_customer") return `¥${value.toFixed(2)}`;
  if (metric === "monthly_transaction_volume") {
    return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}万`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

interface Props {
  anomaly: AnomalyFinding;
  casesById?: Record<string, CaseMeta>;
  onOpenCase?: (id: string) => void;
}

export function AnomalyCard({ anomaly, casesById, onOpenCase }: Props) {
  const label = METRIC_LABEL[anomaly.metric] ?? anomaly.metric;

  return (
    <div className={`border rounded-lg p-3 ${SEVERITY_STYLE[anomaly.severity]}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="font-semibold text-sm">
          {SEVERITY_EMOJI[anomaly.severity]} {anomaly.region} · {label}
        </div>
        <div className="text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded bg-white/60">
          {SEVERITY_LABEL[anomaly.severity]} / {anomaly.severity}
        </div>
      </div>
      <div className="text-sm mt-2 space-y-1">
        <div className="font-mono text-xs opacity-80">期间: {anomaly.period}</div>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
          <span>
            当前:{" "}
            <span className="font-semibold">
              {formatValue(anomaly.metric, anomaly.current_value)}
            </span>
          </span>
          <span>
            历史均值:{" "}
            <span className="font-mono">
              {formatValue(anomaly.metric, anomaly.historical_mean)}
            </span>
          </span>
          <span>
            偏离: <span className="font-semibold">{anomaly.deviation_sigma}σ</span>
          </span>
          {anomaly.baseline_value !== null && (
            <span>
              行业基准:{" "}
              <span className="font-mono">
                {formatValue(anomaly.metric, anomaly.baseline_value)}
              </span>
            </span>
          )}
        </div>
        {anomaly.root_cause_hypothesis && (
          <div className="text-xs mt-2 bg-white/60 p-2 rounded leading-relaxed">
            <span className="font-semibold">根因推测：</span>
            {anomaly.root_cause_hypothesis}
          </div>
        )}
        {anomaly.references.length > 0 && (
          <div className="mt-2">
            <div className="text-[11px] font-semibold text-slate-600 mb-1">
              📚 参考案例 ({anomaly.references.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {anomaly.references.map((refId) => {
                const meta = casesById?.[refId];
                const title = meta?.title ?? refId;
                return (
                  <button
                    key={refId}
                    type="button"
                    onClick={() => onOpenCase?.(refId)}
                    disabled={!onOpenCase}
                    className="text-[11px] px-2 py-1 rounded bg-white/80 border border-slate-300 hover:border-indigo-400 hover:bg-indigo-50 hover:text-indigo-700 transition-colors text-slate-700 disabled:cursor-default"
                    title={meta?.snippet ?? refId}
                  >
                    {title}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
