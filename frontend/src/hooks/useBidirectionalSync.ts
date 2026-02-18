/**
 * useBidirectionalSync — orchestrates code ↔ canvas synchronization.
 *
 * Code → Canvas: CodeEditor onChange (debounced 500ms) → parse code → update diagramStore
 * Canvas → Code: canvas action → wsClient → receive code.sync → update codeStore
 */

import { useEffect, useRef, useCallback } from "react";
import { useDiagramStore } from "@/stores/diagramStore";
import { useCodeStore } from "@/stores/codeStore";
import { useSessionStore } from "@/stores/sessionStore";
import { wsClient } from "@/services/wsClient";
import { parseDiagramCode } from "@/services/codeParser";
import { computeLayout } from "@/services/graphvizLayout";
import type { GraphModel } from "@/types/diagram";

const DEBOUNCE_MS = 500;

export function useBidirectionalSync() {
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isExternalUpdateRef = useRef(false);

  const setGraphModel = useDiagramStore((s) => s.setGraphModel);
  const setSourceCode = useCodeStore((s) => s.setSourceCode);
  const setErrors = useCodeStore((s) => s.setErrors);
  const clearErrors = useCodeStore((s) => s.clearErrors);
  const diagramId = useSessionStore((s) => s.diagramId);
  const setConnected = useSessionStore((s) => s.setConnected);

  // Connect WebSocket when diagramId changes
  useEffect(() => {
    if (!diagramId) return;

    wsClient.connect(diagramId);
    setConnected(true);

    // Handle session init
    const offInit = wsClient.on("session.init", (payload) => {
      if (payload.source_code) {
        isExternalUpdateRef.current = true;
        setSourceCode(payload.source_code);
        const model = parseDiagramCode(payload.source_code);
        setGraphModel(model);
      }
    });

    // Handle render results from code updates
    const offRender = wsClient.on("render.result", (payload) => {
      clearErrors();
      if (payload.graph_model) {
        setGraphModel(payload.graph_model);
      }
    });

    // Handle validation errors
    const offValidation = wsClient.on("validation.error", (payload) => {
      setErrors(payload.errors || []);
    });

    // Handle code sync from canvas actions
    const offSync = wsClient.on("code.sync", (payload) => {
      if (payload.source_code) {
        isExternalUpdateRef.current = true;
        setSourceCode(payload.source_code);
      }
    });

    return () => {
      offInit();
      offRender();
      offValidation();
      offSync();
      wsClient.disconnect();
      setConnected(false);
    };
  }, [diagramId, setGraphModel, setSourceCode, setErrors, clearErrors, setConnected]);

  /**
   * Handle code editor changes — debounced, sends to WebSocket.
   */
  const handleCodeChange = useCallback(
    (code: string) => {
      // Skip if this update came from the server (canvas→code sync)
      if (isExternalUpdateRef.current) {
        isExternalUpdateRef.current = false;
        return;
      }

      if (debounceRef.current) clearTimeout(debounceRef.current);

      debounceRef.current = setTimeout(() => {
        // Parse locally for immediate feedback
        const model = parseDiagramCode(code);
        setGraphModel(model);

        // Send to server for validation + rendering
        if (wsClient.isConnected) {
          wsClient.sendCodeUpdate(code);
        }
      }, DEBOUNCE_MS);
    },
    [setGraphModel],
  );

  return { handleCodeChange };
}
