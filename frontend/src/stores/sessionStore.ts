/**
 * Zustand store for session state — diagram ID, auto-save timer, connection status.
 */

import { create } from "zustand";

interface SessionState {
  diagramId: string | null;
  isConnected: boolean;
  lastSavedAt: string | null;
  isLoading: boolean;

  setDiagramId: (id: string | null) => void;
  setConnected: (connected: boolean) => void;
  setLastSavedAt: (timestamp: string) => void;
  setLoading: (loading: boolean) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  diagramId: null,
  isConnected: false,
  lastSavedAt: null,
  isLoading: false,

  setDiagramId: (id) => set({ diagramId: id }),
  setConnected: (connected) => set({ isConnected: connected }),
  setLastSavedAt: (timestamp) => set({ lastSavedAt: timestamp }),
  setLoading: (loading) => set({ isLoading: loading }),
}));
