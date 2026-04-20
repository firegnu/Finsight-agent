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
            className="text-xs px-2.5 py-1 rounded-sm border border-ink-200 bg-paper-50 text-ink-600 hover:bg-paper-200 hover:border-ink-300 disabled:opacity-50 transition-colors"
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
          placeholder="💬 请输入分析需求，或点击上方示例…"
          className="flex-1 border border-ink-300 rounded-sm px-4 py-2 bg-paper-50 text-ink-900 placeholder:text-ink-400 focus:outline-none focus:border-seal focus:ring-1 focus:ring-seal/40 disabled:bg-paper-100 disabled:text-ink-400 transition-colors"
          disabled={disabled}
        />
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="px-6 py-2 rounded-sm bg-seal text-paper-50 font-medium tracking-wide hover:bg-seal-600 disabled:bg-ink-300 disabled:text-paper-50 disabled:cursor-not-allowed transition-colors"
        >
          {disabled ? (
            <span className="inline-flex items-center gap-2">
              <span className="inline-block w-3 h-3 border-2 border-paper-50/60 border-t-paper-50 rounded-full animate-spin" />
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
