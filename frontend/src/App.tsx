import { useEffect, useMemo, useState } from "react";
import { CaseDetailModal } from "./components/CaseDetailModal";
import { ChatInput } from "./components/ChatInput";
import { Header } from "./components/Header";
import { KPICards } from "./components/KPICards";
import { ReasoningPanel } from "./components/ReasoningPanel";
import { ReportPanel } from "./components/ReportPanel";
import { SkillDetailModal } from "./components/SkillDetailModal";
import { TraceHistoryModal } from "./components/TraceHistoryModal";
import { useCases } from "./hooks/useCases";
import { useProviders } from "./hooks/useProviders";
import { useSkills } from "./hooks/useSkills";
import { useSSE } from "./hooks/useSSE";
import type { AnalysisReport } from "./types";

const PROVIDER_STORAGE_KEY = "finsight.provider_id";

export default function App() {
  const { events, status, error, analyze } = useSSE();
  const cases = useCases();
  const skills = useSkills();
  const providersState = useProviders();
  const [input, setInput] = useState("");
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  const [selectedSkillName, setSelectedSkillName] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(
    () => localStorage.getItem(PROVIDER_STORAGE_KEY),
  );

  // Once providers load, reconcile the stored selection: drop it if the
  // stored id isn't in the server-returned registry (prevents stale keys
  // from older .env configs).
  useEffect(() => {
    if (providersState.loading || providersState.providers.length === 0) return;
    const ids = new Set(providersState.providers.map((p) => p.id));
    if (!selectedProviderId || !ids.has(selectedProviderId)) {
      const fallback = providersState.defaultId ?? providersState.providers[0].id;
      setSelectedProviderId(fallback);
    }
  }, [providersState.loading, providersState.providers, providersState.defaultId, selectedProviderId]);

  // Persist selection across reloads.
  useEffect(() => {
    if (selectedProviderId) {
      localStorage.setItem(PROVIDER_STORAGE_KEY, selectedProviderId);
    }
  }, [selectedProviderId]);

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
    analyze(q, selectedProviderId);
  };

  return (
    <div className="h-full flex flex-col bg-slate-50">
      <Header
        caseCount={cases.cases.length}
        skillCount={skills.skills.length}
        onOpenHistory={() => setHistoryOpen(true)}
        providers={providersState.providers}
        selectedProviderId={selectedProviderId}
        onProviderChange={setSelectedProviderId}
        providerSwitcherDisabled={status === "running"}
      />
      <div className="flex-none p-4 border-b border-slate-200 bg-white">
        <KPICards />
      </div>
      <div className="flex-1 flex min-h-0">
        <div className="w-2/5 border-r border-slate-200 bg-white overflow-hidden">
          <ReasoningPanel
            events={events}
            status={status}
            error={error}
            onOpenCase={setSelectedCaseId}
            onOpenSkill={setSelectedSkillName}
          />
        </div>
        <div className="flex-1 overflow-hidden bg-white">
          <ReportPanel
            report={report}
            status={status}
            casesById={cases.byId}
            onOpenCase={setSelectedCaseId}
          />
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
      <CaseDetailModal
        caseId={selectedCaseId}
        onClose={() => setSelectedCaseId(null)}
      />
      <SkillDetailModal
        name={selectedSkillName}
        onClose={() => setSelectedSkillName(null)}
      />
      <TraceHistoryModal
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
      />
    </div>
  );
}
