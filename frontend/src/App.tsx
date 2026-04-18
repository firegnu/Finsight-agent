import { useMemo, useState } from "react";
import { ChatInput } from "./components/ChatInput";
import { Header } from "./components/Header";
import { KPICards } from "./components/KPICards";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { ReportPanel } from "./components/ReportPanel";
import { useSSE } from "./hooks/useSSE";
import type { AnalysisReport } from "./types";

export default function App() {
  const { events, status, error, analyze } = useSSE();
  const [input, setInput] = useState("");

  const report = useMemo<AnalysisReport | null>(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      if (events[i].type === "report") {
        return events[i].data as unknown as AnalysisReport;
      }
    }
    return null;
  }, [events]);

  const onSend = () => {
    const q = input.trim();
    if (!q || status === "running") return;
    analyze(q);
  };

  return (
    <div className="h-full flex flex-col bg-slate-50">
      <Header />
      <div className="flex-none p-4 border-b border-slate-200 bg-white">
        <KPICards />
      </div>
      <div className="flex-1 flex min-h-0">
        <div className="w-2/5 border-r border-slate-200 bg-white overflow-hidden">
          <ReasoningPanel events={events} status={status} error={error} />
        </div>
        <div className="flex-1 overflow-hidden bg-white">
          <ReportPanel report={report} status={status} />
        </div>
      </div>
      <div className="flex-none p-4 border-t border-slate-200 bg-white">
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={onSend}
          disabled={status === "running"}
        />
      </div>
    </div>
  );
}
