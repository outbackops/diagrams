import React from "react";

interface ToolbarProps {
  onImportClick?: () => void;
  onExportClick?: () => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  onImportClick,
  onExportClick,
}) => {
  return (
    <header className="flex h-12 items-center justify-between border-b border-gray-200 bg-white px-4">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold text-gray-800">Diagram Agent</h1>
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={onImportClick}
          className="rounded px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
        >
          Import
        </button>
        <button
          onClick={onExportClick}
          className="rounded px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
        >
          Export
        </button>
      </div>
    </header>
  );
};
