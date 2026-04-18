import { useEffect, useState } from "react";
import type { HealthResponse } from "../types";
import { fetchHealth } from "../utils/api";

export function Header() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const modelLabel = health ? `${health.model} · ${health.provider}` : "loading…";

  return (
    <header className="flex items-center justify-between px-6 h-14 border-b border-slate-200 bg-white">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-sm font-bold">
          F
        </div>
        <h1 className="text-lg font-semibold text-slate-800">FinSight Agent</h1>
        <span className="text-xs text-slate-400 hidden sm:inline">
          金融数据智能分析
        </span>
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
        <span
          className={`w-2 h-2 rounded-full ${health ? "bg-green-500" : "bg-slate-300"}`}
        />
        <span>Model: {modelLabel}</span>
      </div>
    </header>
  );
}
