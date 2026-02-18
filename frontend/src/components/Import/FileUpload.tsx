/**
 * FileUpload — drag-and-drop area, format detection, upload to /import/file.
 */

import React, { useState, useCallback, useRef } from "react";
import type { IaCFormat } from "@/types/api";

const FORMAT_EXTENSIONS: Record<string, IaCFormat> = {
  tf: "terraform",
  "tf.json": "terraform",
  json: "cloudformation",
  yaml: "cloudformation",
  yml: "cloudformation",
  bicep: "bicep",
};

interface FileUploadProps {
  onImport: (file: File, format: IaCFormat) => void;
  isLoading?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onImport,
  isLoading = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<IaCFormat>("terraform");
  const inputRef = useRef<HTMLInputElement>(null);

  const detectFormat = (filename: string): IaCFormat => {
    const lower = filename.toLowerCase();
    if (lower.endsWith(".tf") || lower.endsWith(".tf.json")) return "terraform";
    if (lower.endsWith(".bicep")) return "bicep";
    if (lower.includes("k8s") || lower.includes("kube")) return "kubernetes";
    return selectedFormat;
  };

  const handleFile = useCallback(
    (file: File) => {
      const format = detectFormat(file.name);
      setSelectedFormat(format);
      onImport(file, format);
    },
    [onImport, selectedFormat],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div className="flex flex-col gap-3 p-4">
      <h3 className="text-sm font-medium text-gray-700">Import from IaC File</h3>

      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors ${
          isDragOver
            ? "border-blue-500 bg-blue-50"
            : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <p className="text-sm text-gray-500">
          {isLoading ? "Processing..." : "Drop a file here or click to browse"}
        </p>
        <p className="mt-1 text-xs text-gray-400">
          .tf, .json, .yaml, .bicep
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".tf,.json,.yaml,.yml,.bicep"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
        className="hidden"
      />

      <select
        value={selectedFormat}
        onChange={(e) => setSelectedFormat(e.target.value as IaCFormat)}
        className="rounded border border-gray-300 px-2 py-1 text-sm"
      >
        <option value="terraform">Terraform</option>
        <option value="cloudformation">CloudFormation</option>
        <option value="bicep">Bicep</option>
        <option value="kubernetes">Kubernetes</option>
      </select>
    </div>
  );
};
