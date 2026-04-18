import type { ActionItem, Priority } from "../types";

const PRIORITY_STYLE: Record<Priority, string> = {
  P0: "bg-red-600 text-white",
  P1: "bg-orange-500 text-white",
  P2: "bg-blue-500 text-white",
  P3: "bg-slate-400 text-white",
};

export function ActionItemCard({ item }: { item: ActionItem }) {
  return (
    <div className="border border-slate-200 rounded-lg p-3 bg-white hover:border-slate-300 transition-colors">
      <div className="flex items-start gap-2">
        <span
          className={`text-xs font-bold px-2 py-0.5 rounded ${PRIORITY_STYLE[item.priority]} shrink-0`}
        >
          {item.priority}
        </span>
        <h3 className="font-semibold text-slate-800 text-sm leading-snug">
          {item.title}
        </h3>
      </div>
      <p className="text-sm text-slate-600 mt-2 leading-relaxed">
        {item.description}
      </p>
      <div className="grid grid-cols-3 gap-3 mt-3 text-xs">
        <Field label="预期影响" value={item.expected_impact} />
        <Field label="建议负责人" value={item.owner_suggestion} />
        <Field label="截止时间" value={item.deadline_suggestion} />
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-semibold text-slate-500 mb-0.5">{label}</div>
      <div className="text-slate-700">{value}</div>
    </div>
  );
}
