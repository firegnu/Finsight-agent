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
      <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-sm p-2">
        加载 KPI 失败：{err}
      </div>
    );
  }
  if (!kpi) {
    return <div className="text-sm text-ink-400 italic">加载指标中…</div>;
  }

  return (
    <div className="flex items-center gap-4">
      <div className="flex flex-col whitespace-nowrap border-r border-ink-200 pr-4">
        <span className="text-[10px] uppercase tracking-widest text-ink-500 font-medium">
          Period
        </span>
        <span className="font-mono text-sm text-ink-800">{kpi.period}</span>
      </div>
      <div className="grid grid-cols-5 gap-3 flex-1">
        {kpi.metrics.map((m, i) => (
          <KPICard key={m.name} metric={m} index={i} />
        ))}
      </div>
    </div>
  );
}

function KPICard({ metric, index }: { metric: KPIMetric; index: number }) {
  const shell = metric.alert
    ? "border-seal-300 bg-seal-50/40"
    : "border-ink-200 bg-paper-50";
  const trendColor =
    metric.trend === "up"
      ? metric.alert
        ? "text-seal-600"
        : "text-emerald-700"
      : metric.trend === "down"
        ? "text-seal-500"
        : "text-ink-500";
  const arrow =
    metric.trend === "up" ? "↑" : metric.trend === "down" ? "↓" : "→";

  return (
    <div
      className={`rounded-sm p-3 border ${shell} transition-colors hover:border-ink-400 animate-print-in`}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-center justify-between gap-1">
        <span className="text-[10px] uppercase tracking-widest text-ink-500 font-medium truncate">
          {metric.name}
        </span>
        {metric.alert && (
          <span
            className="inline-block w-1.5 h-1.5 rounded-full bg-seal animate-pulse"
            title="异常告警"
          />
        )}
      </div>
      <div className="font-mono text-2xl font-medium text-ink-900 mt-1.5 leading-none">
        {metric.value}
      </div>
      <div className={`text-xs mt-1.5 font-mono ${trendColor}`}>
        {arrow} {metric.change}
      </div>
    </div>
  );
}
