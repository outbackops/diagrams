/**
 * ErrorMarker — display inline error indicators from validation.error
 * WebSocket messages. Shows a summary bar below the editor.
 */

import React from "react";
import { useCodeStore } from "@/stores/codeStore";

export const ErrorMarker: React.FC = () => {
  const errors = useCodeStore((s) => s.errors);

  if (errors.length === 0) return null;

  const errorCount = errors.filter((e) => e.severity === "error").length;
  const warningCount = errors.filter((e) => e.severity === "warning").length;

  return (
    <div className="flex items-center gap-2 border-t border-red-200 bg-red-50 px-3 py-1 text-xs">
      {errorCount > 0 && (
        <span className="text-red-600">
          {errorCount} error{errorCount !== 1 ? "s" : ""}
        </span>
      )}
      {warningCount > 0 && (
        <span className="text-amber-600">
          {warningCount} warning{warningCount !== 1 ? "s" : ""}
        </span>
      )}
      <span className="text-gray-500">|</span>
      <span className="truncate text-gray-600">{errors[0].message}</span>
    </div>
  );
};
