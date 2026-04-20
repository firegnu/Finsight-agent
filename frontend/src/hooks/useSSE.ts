import { useCallback, useRef, useState } from "react";
import type { AgentStatus, SSEEvent } from "../types";

// Reads the Server-Sent Events stream from POST /api/analyze.
// EventSource doesn't support POST, so we use fetch + ReadableStream and
// split the body on the SSE "\n\n" event delimiter ourselves.
export function useSSE() {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  // Monotonic timestamp of the last SSE event (or stream start). Drives the
  // WaitingIndicator's elapsed counter — its `key={lastEventAt}` forces a
  // remount each time a new event arrives so the counter resets to 0.
  const [lastEventAt, setLastEventAt] = useState<number>(0);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setEvents([]);
    setError(null);
    setStatus("idle");
  }, []);

  const analyze = useCallback(
    async (query: string, providerId?: string | null) => {
      setEvents([]);
      setError(null);
      setStatus("running");
      setLastEventAt(Date.now());

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      try {
        const body: Record<string, unknown> = { query };
        if (providerId) body.provider_id = providerId;
        const resp = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: ctrl.signal,
        });
        if (!resp.ok || !resp.body) {
          throw new Error(`analyze failed: HTTP ${resp.status}`);
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let sawError = false;

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let idx: number;
          while ((idx = buffer.indexOf("\n\n")) !== -1) {
            const raw = buffer.slice(0, idx).trim();
            buffer = buffer.slice(idx + 2);
            if (!raw.startsWith("data:")) continue;
            const json = raw.replace(/^data:\s*/, "");
            try {
              const event = JSON.parse(json) as SSEEvent;
              setEvents((prev) => [...prev, event]);
              setLastEventAt(Date.now());
              if (event.type === "error") {
                sawError = true;
                const msg =
                  typeof event.data?.msg === "string"
                    ? event.data.msg
                    : "Unknown error";
                setError(msg);
                setStatus("error");
              }
              if (event.type === "done" && !sawError) {
                setStatus("done");
              }
            } catch (e) {
              console.warn("Bad SSE payload:", json, e);
            }
          }
        }
      } catch (e) {
        if ((e as { name?: string }).name === "AbortError") {
          setStatus("idle");
        } else {
          setStatus("error");
          setError((e as Error).message);
        }
      }
    },
    [],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  return { events, status, error, analyze, abort, reset, lastEventAt };
}
