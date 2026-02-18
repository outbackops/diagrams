/**
 * RepoConnect — URL input, branch selection, file list with checkboxes, confirm button.
 */

import React, { useState, useCallback } from "react";
import { apiClient } from "@/services/apiClient";
import type { RepoScanResponse } from "@/types/api";

interface RepoConnectProps {
  onConfirm: (repoUrl: string, selectedFiles: string[]) => void;
  isLoading?: boolean;
}

export const RepoConnect: React.FC<RepoConnectProps> = ({
  onConfirm,
  isLoading = false,
}) => {
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [scanResult, setScanResult] = useState<RepoScanResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [scanning, setScanning] = useState(false);

  const handleScan = useCallback(async () => {
    if (!repoUrl.trim()) return;
    setScanning(true);
    try {
      const result = await apiClient.importRepository({
        repo_url: repoUrl,
        branch,
      });
      setScanResult(result);
      setSelectedFiles(new Set(result.files.map((f) => f.path)));
    } catch {
      setScanResult(null);
    } finally {
      setScanning(false);
    }
  }, [repoUrl, branch]);

  const toggleFile = (path: string) => {
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  return (
    <div className="flex flex-col gap-3 p-4">
      <h3 className="text-sm font-medium text-gray-700">
        Connect Repository
      </h3>

      <input
        type="url"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
        placeholder="https://github.com/user/repo"
        className="rounded border border-gray-300 px-3 py-1.5 text-sm"
      />

      <div className="flex gap-2">
        <input
          type="text"
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          placeholder="Branch"
          className="flex-1 rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        <button
          onClick={handleScan}
          disabled={!repoUrl.trim() || scanning}
          className="rounded bg-gray-600 px-3 py-1.5 text-sm text-white hover:bg-gray-700 disabled:bg-gray-300"
        >
          {scanning ? "Scanning..." : "Scan"}
        </button>
      </div>

      {scanResult && (
        <>
          <div className="max-h-40 overflow-auto rounded border border-gray-200 p-2">
            {scanResult.files.length === 0 ? (
              <p className="text-xs text-gray-500">No IaC files found</p>
            ) : (
              scanResult.files.map((file) => (
                <label
                  key={file.path}
                  className="flex items-center gap-2 py-0.5 text-xs"
                >
                  <input
                    type="checkbox"
                    checked={selectedFiles.has(file.path)}
                    onChange={() => toggleFile(file.path)}
                  />
                  <span>{file.path}</span>
                  <span className="text-gray-400">
                    ({file.format}, {file.resource_count} resources)
                  </span>
                </label>
              ))
            )}
          </div>

          <button
            onClick={() => onConfirm(repoUrl, [...selectedFiles])}
            disabled={selectedFiles.size === 0 || isLoading}
            className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white hover:bg-blue-700 disabled:bg-gray-300"
          >
            Generate Diagram
          </button>
        </>
      )}
    </div>
  );
};
