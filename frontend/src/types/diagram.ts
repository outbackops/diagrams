/**
 * Diagram graph model types — the in-memory representation of a diagram
 * used by the React Flow canvas and Zustand stores.
 *
 * These are the frontend runtime types; the persisted form is Python source code.
 * See data-model.md for entity definitions.
 */

export interface DiagramNode {
  /** Unique identifier — maps to Python variable name */
  id: string;
  /** Cloud provider (e.g., "aws", "azure", "gcp", "custom") */
  provider: string;
  /** Service category (e.g., "compute", "database") */
  category: string;
  /** Service class name (e.g., "EC2", "Lambda", "AKS") */
  service: string;
  /** Display label — defaults to service name */
  label: string;
  /** Path to icon asset in public/icons/ */
  iconPath: string;
  /** Parent cluster ID (null if top-level) */
  clusterId: string | null;
  /** Canvas position from layout or drag */
  position: Position;
}

export interface DiagramEdge {
  /** Unique identifier */
  id: string;
  /** Source node ID */
  sourceNodeId: string;
  /** Target node ID */
  targetNodeId: string;
  /** Arrow direction — maps to >>, <<, -, Edge attrs */
  direction: EdgeDirection;
  /** Edge label text */
  label: string | null;
  /** Edge style */
  style: EdgeStyle | null;
  /** Edge color */
  color: string | null;
}

export interface DiagramCluster {
  /** Unique identifier */
  id: string;
  /** Display label — maps to Cluster label parameter */
  label: string;
  /** Parent cluster ID for nesting (null if top-level) */
  parentClusterId: string | null;
  /** Nesting depth (0–3, max 4 levels per Constitution IV) */
  depth: number;
  /** Node IDs contained in this cluster */
  nodeIds: string[];
  /** Nested child cluster IDs */
  childClusterIds: string[];
}

export interface GraphModel {
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  clusters: DiagramCluster[];
}

export interface Position {
  x: number;
  y: number;
}

export type EdgeDirection = "forward" | "reverse" | "both" | "none";

export type EdgeStyle = "solid" | "dashed" | "dotted" | "bold";

/**
 * WebSocket message types per contracts/websocket.md
 */
export type WsMessageType =
  | "code.update"
  | "canvas.update"
  | "autosave.request"
  | "ping"
  | "session.init"
  | "render.result"
  | "code.sync"
  | "validation.error"
  | "autosave.ack"
  | "pong"
  | "error";

export interface WsMessage<T = unknown> {
  type: WsMessageType;
  id?: string;
  payload: T;
}

export type CanvasAction =
  | { action: "move_node"; node_id: string; position: Position }
  | { action: "rename_node"; node_id: string; label: string }
  | {
      action: "add_edge";
      source_id: string;
      target_id: string;
      direction: EdgeDirection;
    }
  | { action: "remove_edge"; edge_id: string }
  | { action: "remove_node"; node_id: string }
  | {
      action: "add_node";
      provider: string;
      category: string;
      service: string;
      label: string;
      cluster_id?: string;
    }
  | {
      action: "create_cluster";
      label: string;
      node_ids: string[];
      parent_cluster_id?: string;
    }
  | { action: "remove_cluster"; cluster_id: string };
