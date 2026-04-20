import type { AnomalyFinding, CaseMeta, Severity } from "../types";

const SEVERITY_STYLE: Record<Severity, string> = {
  critical: "bg-red-50 border-red-400/80 text-red-900",
  high: "bg-orange-50 border-orange-400/80 text-orange-900",
  medium: "bg-amber-50 border-amber-400/80 text-amber-900",
  low: "bg-sky-50 border-sky-400/80 text-sky-900",
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
    <div
      className={`border rounded-sm p-3 ${SEVERITY_STYLE[anomaly.severity]}`}
    >
      <div className="flex items-center justify-between gap-2 pb-2 border-b border-current/15">
        <div className="font-serif font-bold text-[15px] tracking-tight">
          {SEVERITY_EMOJI[anomaly.severity]} {anomaly.region} · {label}
        </div>
        <div className="text-[10px] uppercase tracking-widest font-mono font-semibold px-1.5 py-0.5 rounded-sm bg-paper-50/70 border border-current/25">
          {SEVERITY_LABEL[anomaly.severity]} / {anomaly.severity}
        </div>
      </div>
      <div className="text-sm mt-2.5 space-y-2">
        <div className="font-mono text-[11px] opacity-75">
          期间 <span className="ml-1">{anomaly.period}</span>
        </div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs">
          <span>
            当前
            <span className="font-mono font-semibold text-base ml-1.5">
              {formatValue(anomaly.metric, anomaly.current_value)}
            </span>
          </span>
          <span className="opacity-85">
            历史均值
            <span className="font-mono ml-1.5">
              {formatValue(anomaly.metric, anomaly.historical_mean)}
            </span>
          </span>
          <span>
            偏离
            <span className="font-mono font-semibold ml-1.5">
              {anomaly.deviation_sigma}σ
            </span>
          </span>
          {anomaly.baseline_value !== null && (
            <span className="opacity-85">
              行业基准
              <span className="font-mono ml-1.5">
                {formatValue(anomaly.metric, anomaly.baseline_value)}
              </span>
            </span>
          )}
        </div>
        {anomaly.root_cause_hypothesis && (
          <div className="text-xs mt-2 bg-paper-50/70 p-2 rounded-sm leading-relaxed font-serif">
            <span className="font-sans font-bold not-italic">根因推测 · </span>
            {anomaly.root_cause_hypothesis}
          </div>
        )}
        {anomaly.references.length > 0 && (
          <div className="mt-2">
            <div className="text-[10px] uppercase tracking-widest font-medium opacity-80 mb-1.5">
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
                    className="text-[11px] px-2 py-0.5 rounded-sm bg-paper-50 border border-current/30 hover:border-current hover:underline underline-offset-2 transition-all disabled:cursor-default"
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
