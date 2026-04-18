const SUGGESTIONS = [
  "信用卡业务上个月有什么异常？",
  "华东区逾期率为什么上升了？",
  "对比各区域 2026-03 的获客量",
];

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSend, disabled }: Props) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onChange(s)}
            disabled={disabled}
            className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-50 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSend();
            }
          }}
          placeholder="💬 请输入分析需求，或点击上方示例..."
          className="flex-1 border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-slate-50 disabled:text-slate-400"
          disabled={disabled}
        />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
        >
          {disabled ? (
            <span className="inline-flex items-center gap-2">
              <span className="inline-block w-3 h-3 border-2 border-white/60 border-t-white rounded-full animate-spin" />
              分析中
            </span>
          ) : (
            "发送"
          )}
        </button>
      </div>
    </div>
  );
}
