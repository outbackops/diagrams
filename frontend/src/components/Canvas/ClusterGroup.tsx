/**
 * ClusterGroup — nested container with themed background and label.
 * Supports up to 4 levels of nesting per Constitution IV.
 */

import React, { memo } from "react";
import { type NodeProps } from "@xyflow/react";

// Theme colors matching diagrams library THEMES
const DEPTH_COLORS = [
  "rgba(229, 245, 253, 0.8)", // depth 0
  "rgba(235, 243, 231, 0.8)", // depth 1
  "rgba(236, 232, 246, 0.8)", // depth 2
  "rgba(253, 247, 227, 0.8)", // depth 3
];

interface ClusterGroupData {
  label: string;
  depth: number;
  [key: string]: unknown;
}

const ClusterGroupComponent: React.FC<NodeProps> = ({ data }) => {
  const clusterData = data as ClusterGroupData;
  const depth = Math.min(clusterData.depth || 0, 3);
  const bgColor = DEPTH_COLORS[depth];

  return (
    <div
      className="rounded-lg border border-gray-300 p-4"
      style={{
        backgroundColor: bgColor,
        minWidth: 200,
        minHeight: 100,
      }}
    >
      <span className="text-xs font-semibold text-gray-600">
        {clusterData.label}
      </span>
    </div>
  );
};

export const ClusterGroup = memo(ClusterGroupComponent);
