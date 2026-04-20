import type { ProviderInfo } from "../types";

interface Props {
  providers: ProviderInfo[];
  selectedId: string | null;
  onChange: (id: string) => void;
  disabled?: boolean;
}

export function ProviderSwitcher({
  providers,
  selectedId,
  onChange,
  disabled = false,
}: Props) {
  if (providers.length === 0) {
    return (
      <div className="flex items-center gap-2 text-slate-400 font-mono text-xs">
        <span className="w-2 h-2 rounded-full bg-slate-300" />
        <span>no provider</span>
      </div>
    );
  }

  const current = providers.find((p) => p.id === selectedId) ?? providers[0];

  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className="w-2 h-2 rounded-full bg-green-500"
        title={`当前模型：${current.model}`}
      />
      <div className="relative">
        <select
          value={current.id}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          className="appearance-none bg-white border border-slate-200 rounded px-2 py-1 pr-6 font-mono text-xs text-slate-700 hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          title={`切换 LLM provider（当前：${current.label}）`}
        >
          {providers.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <svg
          className="pointer-events-none absolute right-1.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path
            d="M3 4.5L6 7.5L9 4.5"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <span className="text-slate-400 font-mono hidden md:inline">
        {current.model}
      </span>
    </div>
  );
}
