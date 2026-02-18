/**
 * useDiagramExport — call export endpoint, handle download and share URL copy.
 */

import { useState, useCallback } from "react";
import { apiClient } from "@/services/apiClient";
import { useSessionStore } from "@/stores/sessionStore";
import type { ExportFormat, ExportResponse } from "@/types/api";

export function useDiagramExport() {
  const [isExporting, setIsExporting] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const diagramId = useSessionStore((s) => s.diagramId);

  const exportDiagram = useCallback(
    async (format: ExportFormat) => {
      if (!diagramId) return;

      setIsExporting(true);
      try {
        const response: ExportResponse = await apiClient.exportDiagram(
          diagramId,
          { format },
        );

        if (response.share_url) {
          setShareUrl(response.share_url);
          return;
        }

        if (response.content_base64) {
          // Decode and trigger download
          const binary = atob(response.content_base64);
          const bytes = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
          }

          const mimeTypes: Record<string, string> = {
            png: "image/png",
            svg: "image/svg+xml",
            pdf: "application/pdf",
            py: "text/x-python",
          };

          const blob = new Blob([bytes], {
            type: mimeTypes[format] || "application/octet-stream",
          });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `diagram.${format}`;
          a.click();
          URL.revokeObjectURL(url);
        }
      } catch (err) {
        console.error("Export failed:", err);
      } finally {
        setIsExporting(false);
      }
    },
    [diagramId],
  );

  return { exportDiagram, isExporting, shareUrl };
}
