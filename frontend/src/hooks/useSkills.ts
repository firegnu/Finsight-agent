import { useEffect, useState } from "react";
import type { SkillMeta } from "../types";
import { fetchSkills } from "../utils/api";

export interface SkillsData {
  skills: SkillMeta[];
  byName: Record<string, SkillMeta>;
  loading: boolean;
  error: string | null;
}

export function useSkills(): SkillsData {
  const [skills, setSkills] = useState<SkillMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchSkills()
      .then((r) => !cancelled && setSkills(r.skills))
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const byName = Object.fromEntries(skills.map((s) => [s.name, s]));
  return { skills, byName, loading, error };
}
