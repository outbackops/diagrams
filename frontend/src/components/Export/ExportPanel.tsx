/**
 * ExportPanel — format selector (PNG/SVG/PDF/Code/Share), download trigger.
 */

import React, { useState } from "react";
import type { ExportFormat } from "@/types/api";

interface ExportPanelProps {
  onExport: (format: ExportFormat) => void;
  shareUrl?: string | null;
  isLoading?: boolean;
}

const FORMATS: { value: ExportFormat; label: string; description: string }[] = [
  { value: "png", label: "PNG", description: "Raster image" },
  { value: "svg", label: "SVG", description: "Vector image" },
  { value: "pdf", label: "PDF", description: "Document" },
  { value: "py", label: "Python Code", description: "Executable .py file" },
  { value: "share", label: "Share Link", description: "Public read-only URL" },
];

export const ExportPanel: React.FC<ExportPanelProps> = ({
  onExport,
  shareUrl,
  isLoading = false,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (shareUrl) {
      await navigator.clipboard.writeText(window.location.origin + shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col gap-3 p-4">
      <h3 className="text-sm font-medium text-gray-700">Export Diagram</h3>

      <div className="flex flex-col gap-1">
        {FORMATS.map((fmt) => (
          <button
            key={fmt.value}
            onClick={() => onExport(fmt.value)}
            disabled={isLoading}
            className="flex items-center justify-between rounded px-3 py-2 text-left text-sm hover:bg-gray-100 disabled:opacity-50"
          >
            <span className="font-medium text-gray-700">{fmt.label}</span>
            <span className="text-xs text-gray-400">{fmt.description}</span>
          </button>
        ))}
      </div>

      {shareUrl && (
        <div className="flex items-center gap-2 rounded bg-green-50 p-2">
          <span className="flex-1 truncate text-xs text-green-700">
            {window.location.origin + shareUrl}
          </span>
          <button
            onClick={handleCopy}
            className="text-xs text-green-600 hover:underline"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
      )}
    </div>
  );
};
