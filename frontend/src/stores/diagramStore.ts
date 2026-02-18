/**
 * Zustand store for diagram graph model — nodes, edges, clusters, CRUD actions.
 * This is the central state for the React Flow canvas.
 */

import { create } from "zustand";
import type {
  DiagramNode,
  DiagramEdge,
  DiagramCluster,
  GraphModel,
} from "@/types/diagram";

interface DiagramState {
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  clusters: DiagramCluster[];

  // Actions
  setGraphModel: (model: GraphModel) => void;
  addNode: (node: DiagramNode) => void;
  updateNode: (id: string, updates: Partial<DiagramNode>) => void;
  removeNode: (id: string) => void;
  addEdge: (edge: DiagramEdge) => void;
  removeEdge: (id: string) => void;
  addCluster: (cluster: DiagramCluster) => void;
  removeCluster: (id: string) => void;
  updateNodePosition: (id: string, x: number, y: number) => void;
  clear: () => void;
}

export const useDiagramStore = create<DiagramState>((set) => ({
  nodes: [],
  edges: [],
  clusters: [],

  setGraphModel: (model) =>
    set({
      nodes: model.nodes,
      edges: model.edges,
      clusters: model.clusters,
    }),

  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),

  updateNode: (id, updates) =>
    set((state) => ({
      nodes: state.nodes.map((n) => (n.id === id ? { ...n, ...updates } : n)),
    })),

  removeNode: (id) =>
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== id),
      edges: state.edges.filter(
        (e) => e.sourceNodeId !== id && e.targetNodeId !== id,
      ),
    })),

  addEdge: (edge) => set((state) => ({ edges: [...state.edges, edge] })),

  removeEdge: (id) =>
    set((state) => ({
      edges: state.edges.filter((e) => e.id !== id),
    })),

  addCluster: (cluster) =>
    set((state) => ({ clusters: [...state.clusters, cluster] })),

  removeCluster: (id) =>
    set((state) => ({
      clusters: state.clusters.filter((c) => c.id !== id),
    })),

  updateNodePosition: (id, x, y) =>
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === id ? { ...n, position: { x, y } } : n,
      ),
    })),

  clear: () => set({ nodes: [], edges: [], clusters: [] }),
}));
