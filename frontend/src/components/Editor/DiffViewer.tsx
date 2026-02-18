/**
 * DiffViewer — Monaco diff editor showing before/after with accept/reject buttons.
 */

import React from "react";
import { DiffEditor } from "@monaco-editor/react";

interface DiffViewerProps {
  original: string;
  modified: string;
  onAccept: () => void;
  onReject: () => void;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  original,
  modified,
  onAccept,
  onReject,
}) => {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-3 py-2">
        <span className="text-sm font-medium text-gray-700">
          Review AI Changes
        </span>
        <div className="flex gap-2">
          <button
            onClick={onReject}
            className="rounded border border-gray-300 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100"
          >
            Reject
          </button>
          <button
            onClick={onAccept}
            className="rounded bg-green-600 px-3 py-1 text-xs text-white hover:bg-green-700"
          >
            Accept Changes
          </button>
        </div>
      </div>
      <div className="flex-1">
        <DiffEditor
          height="100%"
          language="python"
          theme="vs-light"
          original={original}
          modified={modified}
          options={{
            readOnly: true,
            renderSideBySide: true,
            minimap: { enabled: false },
            fontSize: 12,
          }}
        />
      </div>
    </div>
  );
};
