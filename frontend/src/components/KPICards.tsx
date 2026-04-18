import { useEffect, useState } from "react";
import type { KPIMetric, KPIResponse } from "../types";
import { fetchKPI } from "../utils/api";

export function KPICards() {
  const [kpi, setKpi] = useState<KPIResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetchKPI()
      .then(setKpi)
      .catch((e: Error) => setErr(e.message));
  }, []);

  if (err) {
    return (
      <div className="text-sm text-red-500 bg-red-50 border border-red-200 rounded p-2">
        加载 KPI 失败：{err}
      </div>
    );
  }
  if (!kpi) {
    return <div className="text-sm text-slate-400">加载指标中...</div>;
  }

  return (
    <div className="flex items-center gap-3">
      <div className="text-xs text-slate-500 font-medium whitespace-nowrap">
        {kpi.period}
      </div>
      <div className="grid grid-cols-5 gap-3 flex-1">
        {kpi.metrics.map((m) => (
          <KPICard key={m.name} metric={m} />
        ))}
      </div>
    </div>
  );
}

function KPICard({ metric }: { metric: KPIMetric }) {
  const borderColor = metric.alert
    ? "border-red-300 bg-red-50"
    : "border-slate-200 bg-white";
  const trendColor =
    metric.trend === "up"
      ? metric.alert
        ? "text-red-600"
        : "text-emerald-600"
      : metric.trend === "down"
        ? "text-red-500"
        : "text-slate-500";
  const arrow =
    metric.trend === "up" ? "↑" : metric.trend === "down" ? "↓" : "→";

  return (
    <div className={`rounded-lg p-3 border ${borderColor} transition-shadow hover:shadow-sm`}>
      <div className="text-xs text-slate-500 flex items-center gap-1">
        {metric.name}
        {metric.alert && (
          <span
            className="inline-block w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"
            title="异常告警"
          />
        )}
      </div>
      <div className="text-xl font-semibold text-slate-800 mt-1">{metric.value}</div>
      <div className={`text-xs mt-1 ${trendColor}`}>
        {metric.change} {arrow}
      </div>
    </div>
  );
}
