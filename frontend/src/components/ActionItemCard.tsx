import type { ActionItem, Priority } from "../types";

const PRIORITY_STYLE: Record<Priority, string> = {
  P0: "bg-seal text-paper-50",
  P1: "bg-orange-700 text-paper-50",
  P2: "bg-ink-700 text-paper-50",
  P3: "bg-ink-400 text-paper-50",
};

export function ActionItemCard({ item }: { item: ActionItem }) {
  return (
    <div className="border border-ink-200 rounded-sm p-3 bg-paper-50 hover:border-ink-400 transition-colors">
      <div className="flex items-start gap-2.5">
        <span
          className={`text-[10px] uppercase tracking-widest font-mono font-bold px-2 py-0.5 rounded-sm ${PRIORITY_STYLE[item.priority]} shrink-0 mt-0.5`}
        >
          {item.priority}
        </span>
        <h3 className="font-serif font-bold text-ink-900 text-[15px] leading-snug tracking-tight">
          {item.title}
        </h3>
      </div>
      <p className="text-sm text-ink-700 mt-2 leading-relaxed">
        {item.description}
      </p>
      <div className="grid grid-cols-3 gap-4 mt-3 pt-2.5 border-t border-ink-200 text-xs">
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
      <div className="text-[10px] uppercase tracking-widest font-medium text-ink-500 mb-0.5">
        {label}
      </div>
      <div className="text-ink-800">{value}</div>
    </div>
  );
}
