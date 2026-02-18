/**
 * DiagramCanvas — React Flow wrapper rendering nodes/edges/clusters from diagramStore.
 * Uses controlled state pattern with applyNodeChanges/applyEdgeChanges for dragging.
 */

import React, { useMemo, useCallback, useState, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type Connection,
  type OnNodesChange,
  type OnEdgesChange,
  type NodeChange,
  type EdgeChange,
  MarkerType,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useDiagramStore } from "@/stores/diagramStore";
import { ProviderNode } from "./ProviderNode";
import { ClusterGroup } from "./ClusterGroup";
import { EdgeConnection } from "./EdgeConnection";
import { wsClient } from "@/services/wsClient";
import type { DiagramNode, DiagramEdge, DiagramCluster, EdgeDirection } from "@/types/diagram";

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
    draggable: true,
    data: {
      label: node.label,
      provider: node.provider,
      category: node.category,
      service: node.service,
      iconPath: node.iconPath,
    },
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
  const storeNodes = useDiagramStore((s) => s.nodes);
  const storeEdges = useDiagramStore((s) => s.edges);
  const storeClusters = useDiagramStore((s) => s.clusters);
  const updateNodePosition = useDiagramStore((s) => s.updateNodePosition);
  const removeNode = useDiagramStore((s) => s.removeNode);
  const removeEdge = useDiagramStore((s) => s.removeEdge);
  const storeAddEdge = useDiagramStore((s) => s.addEdge);

  // React Flow controlled state — this is what makes dragging work
  const [rfNodes, setRfNodes] = useState<Node[]>([]);
  const [rfEdges, setRfEdges] = useState<Edge[]>([]);

  // Sync store → React Flow state when store changes (new diagram loaded)
  useEffect(() => {
    const newNodes = storeNodes.map(toReactFlowNode);
    setRfNodes(newNodes);
  }, [storeNodes]);

  useEffect(() => {
    setRfEdges(storeEdges.map(toReactFlowEdge));
  }, [storeEdges]);

  // Handle node changes (drag, select, remove) — this is the key for draggability
  const onNodesChange: OnNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setRfNodes((nds) => applyNodeChanges(changes, nds));

      // Sync position changes back to store
      for (const change of changes) {
        if (change.type === "position" && change.position && change.dragging === false) {
          updateNodePosition(change.id, change.position.x, change.position.y);
          if (wsClient.isConnected) {
            wsClient.sendCanvasUpdate({
              action: "move_node",
              node_id: change.id,
              position: { x: change.position.x, y: change.position.y },
            });
          }
        }
      }
    },
    [updateNodePosition],
  );

  // Handle edge changes (select, remove)
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setRfEdges((eds) => applyEdgeChanges(changes, eds));

      for (const change of changes) {
        if (change.type === "remove") {
          removeEdge(change.id);
          if (wsClient.isConnected) {
            wsClient.sendCanvasUpdate({ action: "remove_edge", edge_id: change.id });
          }
        }
      }
    },
    [removeEdge],
  );

  // Edge drawing — React Flow onConnect
  const handleConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const newEdge: DiagramEdge = {
        id: `edge_${Date.now()}`,
        sourceNodeId: connection.source,
        targetNodeId: connection.target,
        direction: "forward" as EdgeDirection,
        label: null,
        style: null,
        color: null,
      };
      storeAddEdge(newEdge);
      if (wsClient.isConnected) {
        wsClient.sendCanvasUpdate({
          action: "add_edge",
          source_id: connection.source,
          target_id: connection.target,
          direction: "forward",
        });
      }
    },
    [storeAddEdge],
  );

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={handleConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        deleteKeyCode="Delete"
        fitView
        fitViewOptions={{ padding: 0.3 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{ animated: true }}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
