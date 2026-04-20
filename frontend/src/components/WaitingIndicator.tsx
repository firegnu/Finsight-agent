import { useEffect, useState } from "react";

interface Props {
  stage: "thinking" | "tool";
}

export function WaitingIndicator({ stage }: Props) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const icon = stage === "tool" ? "🔧" : "🧠";
  const baseLabel = stage === "tool" ? "工具执行中" : "大模型思考中";
  const label =
    elapsed < 15
      ? `${baseLabel}…`
      : elapsed < 45
        ? "等待模型响应…"
        : "免费档响应较慢，请耐心等待…";

  return (
    <div className="text-sm text-slate-600 italic border-l-2 border-indigo-300 pl-3 py-1.5 bg-indigo-50/40 rounded-r flex items-center gap-2">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
      </span>
      <span>
        {icon} {label}（{elapsed}s）
      </span>
    </div>
  );
}
