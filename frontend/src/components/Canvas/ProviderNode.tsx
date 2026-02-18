/**
 * ProviderNode — custom React Flow node rendering a provider icon + label.
 *
 * Supports all 17+ providers in the diagrams library plus custom nodes (T092).
 * Custom nodes (provider === "custom") render arbitrary icon_path without
 * provider/category lookup.
 */

import React, { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";

interface ProviderNodeData {
  label: string;
  provider: string;
  category: string;
  service: string;
  iconPath: string;
  [key: string]: unknown;
}

const ProviderNodeComponent: React.FC<NodeProps> = ({ data, selected }) => {
  const nodeData = data as ProviderNodeData;

  // Normalize icon path: strip "resources/" prefix if present, ensure /icons/ prefix
  let iconSrc = "";
  if (nodeData.provider === "custom") {
    iconSrc = nodeData.iconPath;
  } else if (nodeData.iconPath) {
    const cleaned = nodeData.iconPath.replace(/^resources\//, "");
    iconSrc = `/icons/${cleaned}`;
  }

  return (
    <div
      className={`flex flex-col items-center gap-1 rounded-lg bg-white p-2 shadow-sm transition-shadow ${
        selected ? "ring-2 ring-blue-500 shadow-md" : "hover:shadow-md"
      }`}
      style={{ minWidth: 80 }}
    >
      <Handle type="target" position={Position.Left} className="!bg-gray-400" />

      {iconSrc && (
        <img
          src={iconSrc}
          alt={nodeData.service}
          className="h-10 w-10 object-contain"
          onError={(e) => {
            // Fallback: hide broken image
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      )}

      <span className="max-w-[120px] truncate text-center text-xs font-medium text-gray-700">
        {nodeData.label || nodeData.service}
      </span>

      <Handle type="source" position={Position.Right} className="!bg-gray-400" />
    </div>
  );
};

export const ProviderNode = memo(ProviderNodeComponent);
