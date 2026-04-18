import { useEffect, useMemo, useState } from "react";
import type { CaseMeta } from "../types";
import { fetchCases } from "../utils/api";

export interface CasesData {
  cases: CaseMeta[];
  byId: Record<string, CaseMeta>;
  loading: boolean;
  error: string | null;
}

export function useCases(): CasesData {
  const [cases, setCases] = useState<CaseMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCases()
      .then((r) => {
        if (!cancelled) setCases(r.cases);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const byId = useMemo(
    () => Object.fromEntries(cases.map((c) => [c.id, c])),
    [cases],
  );

  return { cases, byId, loading, error };
}
