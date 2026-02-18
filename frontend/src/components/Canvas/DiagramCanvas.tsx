/**
 * DiagramCanvas — React Flow wrapper rendering nodes/edges/clusters from diagramStore.
 */

import React, { useMemo, useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type Connection,
  type NodeDragHandler,
  type OnNodesDelete,
  type OnEdgesDelete,
  MarkerType,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useDiagramStore } from "@/stores/diagramStore";
import { ProviderNode } from "./ProviderNode";
import { ClusterGroup } from "./ClusterGroup";
import { EdgeConnection } from "./EdgeConnection";
import { wsClient } from "@/services/wsClient";
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
  const updateNodePosition = useDiagramStore((s) => s.updateNodePosition);
  const removeNode = useDiagramStore((s) => s.removeNode);
  const removeEdge = useDiagramStore((s) => s.removeEdge);
  const addEdge = useDiagramStore((s) => s.addEdge);

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

  // T048: Drag-to-reposition — update layout sidecar via WebSocket
  const handleNodeDragStop: NodeDragHandler = useCallback(
    (_event, node) => {
      updateNodePosition(node.id, node.position.x, node.position.y);
      if (wsClient.isConnected) {
        wsClient.sendCanvasUpdate({
          action: "move_node",
          node_id: node.id,
          position: { x: node.position.x, y: node.position.y },
        });
      }
    },
    [updateNodePosition],
  );

  // T050: Edge drawing — React Flow onConnect
  const handleConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const newEdge = {
        id: `edge_${Date.now()}`,
        sourceNodeId: connection.source,
        targetNodeId: connection.target,
        direction: "forward" as EdgeDirection,
        label: null,
        style: null,
        color: null,
      };
      addEdge(newEdge);
      if (wsClient.isConnected) {
        wsClient.sendCanvasUpdate({
          action: "add_edge",
          source_id: connection.source,
          target_id: connection.target,
          direction: "forward",
        });
      }
    },
    [addEdge],
  );

  // T051: Node delete handler
  const handleNodesDelete: OnNodesDelete = useCallback(
    (deleted) => {
      for (const node of deleted) {
        removeNode(node.id);
        if (wsClient.isConnected) {
          wsClient.sendCanvasUpdate({
            action: "remove_node",
            node_id: node.id,
          });
        }
      }
    },
    [removeNode],
  );

  // T051: Edge delete handler
  const handleEdgesDelete: OnEdgesDelete = useCallback(
    (deleted) => {
      for (const edge of deleted) {
        removeEdge(edge.id);
        if (wsClient.isConnected) {
          wsClient.sendCanvasUpdate({
            action: "remove_edge",
            edge_id: edge.id,
          });
        }
      }
    },
    [removeEdge],
  );

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeDragStop={handleNodeDragStop}
        onConnect={handleConnect}
        onNodesDelete={handleNodesDelete}
        onEdgesDelete={handleEdgesDelete}
        deleteKeyCode="Delete"
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
