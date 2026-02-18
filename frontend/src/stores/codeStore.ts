/**
 * Zustand store for code editor state — source code, dirty flag, error markers.
 */

import { create } from "zustand";
import type { ValidationError } from "@/types/api";

interface CodeState {
  sourceCode: string;
  isDirty: boolean;
  errors: ValidationError[];

  setSourceCode: (code: string) => void;
  setErrors: (errors: ValidationError[]) => void;
  clearErrors: () => void;
  markClean: () => void;
}

export const useCodeStore = create<CodeState>((set) => ({
  sourceCode: "",
  isDirty: false,
  errors: [],

  setSourceCode: (code) => set({ sourceCode: code, isDirty: true }),

  setErrors: (errors) => set({ errors }),

  clearErrors: () => set({ errors: [] }),

  markClean: () => set({ isDirty: false }),
}));
