/**
 * useAutoSave — periodic autosave.request every 30s via WebSocket,
 * restore on reconnect.
 */

import { useEffect, useRef } from "react";
import { useCodeStore } from "@/stores/codeStore";
import { useSessionStore } from "@/stores/sessionStore";
import { wsClient } from "@/services/wsClient";

const AUTO_SAVE_INTERVAL_MS = 30_000;

export function useAutoSave() {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sourceCode = useCodeStore((s) => s.sourceCode);
  const isDirty = useCodeStore((s) => s.isDirty);
  const markClean = useCodeStore((s) => s.markClean);
  const diagramId = useSessionStore((s) => s.diagramId);
  const setLastSavedAt = useSessionStore((s) => s.setLastSavedAt);
  const isConnected = useSessionStore((s) => s.isConnected);

  useEffect(() => {
    if (!diagramId || !isConnected) return;

    // Listen for autosave acknowledgements
    const off = wsClient.on("autosave.ack", (payload) => {
      if (payload.saved_at) {
        setLastSavedAt(payload.saved_at);
        markClean();
      }
    });

    // Start periodic auto-save
    timerRef.current = setInterval(() => {
      if (isDirty && wsClient.isConnected) {
        wsClient.sendAutoSave(sourceCode, null);
      }
    }, AUTO_SAVE_INTERVAL_MS);

    return () => {
      off();
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [diagramId, isConnected, isDirty, sourceCode, markClean, setLastSavedAt]);
}
