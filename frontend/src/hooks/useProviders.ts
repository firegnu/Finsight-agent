import { useEffect, useState } from "react";
import type { ProviderInfo } from "../types";
import { fetchProviders } from "../utils/api";

export interface UseProvidersResult {
  providers: ProviderInfo[];
  defaultId: string | null;
  loading: boolean;
  error: string | null;
}

export function useProviders(): UseProvidersResult {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [defaultId, setDefaultId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchProviders()
      .then((res) => {
        if (!mounted) return;
        setProviders(res.providers);
        setDefaultId(res.default_provider_id);
      })
      .catch((e: Error) => mounted && setError(e.message))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  return { providers, defaultId, loading, error };
}
