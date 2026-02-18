/**
 * DiagramCanvas — React Flow wrapper rendering nodes/edges/clusters from diagramStore.
 */

import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useDiagramStore } from "@/stores/diagramStore";
import { ProviderNode } from "./ProviderNode";
import { ClusterGroup } from "./ClusterGroup";
import { EdgeConnection } from "./EdgeConnection";
import type { DiagramNode, DiagramEdge, EdgeDirection } from "@/types/diagram";

// Register custom node and edge types
const nodeTypes = {
  providerNode: ProviderNode,
  clusterGroup: ClusterGroup,
};

const edgeTypes = {
  edgeConnection: EdgeConnection,
};

function toReactFlowNode(node: DiagramNode): Node {
  return {
    id: node.id,
    type: "providerNode",
    position: node.position,
    data: {
      label: node.label,
      provider: node.provider,
      category: node.category,
      service: node.service,
      iconPath: node.iconPath,
    },
    parentId: node.clusterId || undefined,
  };
}

function directionToMarker(direction: EdgeDirection) {
  switch (direction) {
    case "forward":
      return { markerEnd: { type: MarkerType.ArrowClosed, color: "#495057" } };
    case "reverse":
      return {
        markerStart: { type: MarkerType.ArrowClosed, color: "#495057" },
      };
    case "both":
      return {
        markerEnd: { type: MarkerType.ArrowClosed, color: "#495057" },
        markerStart: { type: MarkerType.ArrowClosed, color: "#495057" },
      };
    default:
      return {};
  }
}

function toReactFlowEdge(edge: DiagramEdge): Edge {
  const markers = directionToMarker(edge.direction);
  return {
    id: edge.id,
    source: edge.sourceNodeId,
    target: edge.targetNodeId,
    type: "edgeConnection",
    label: edge.label || undefined,
    ...markers,
  };
}

export const DiagramCanvas: React.FC = () => {
  const { nodes, edges, clusters } = useDiagramStore();

  const rfNodes: Node[] = useMemo(() => {
    const clusterNodes: Node[] = clusters.map((cluster) => ({
      id: cluster.id,
      type: "clusterGroup",
      position: { x: 0, y: 0 },
      data: { label: cluster.label, depth: cluster.depth },
      parentId: cluster.parentClusterId || undefined,
      style: { width: 300, height: 200 },
    }));

    const diagramNodes = nodes.map(toReactFlowNode);
    return [...clusterNodes, ...diagramNodes];
  }, [nodes, clusters]);

  const rfEdges: Edge[] = useMemo(() => edges.map(toReactFlowEdge), [edges]);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
