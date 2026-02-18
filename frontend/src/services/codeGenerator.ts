/**
 * Graph model → Python code generator.
 *
 * PLACEMENT RATIONALE (T097): This service is intentionally implemented in
 * Phase 5 (User Story 3 — Interactive Visual Canvas) because:
 *
 * - US2 (Phase 4) only requires code → canvas direction (codeParser.ts)
 * - Canvas → code direction (this file) is only needed when the user makes
 *   visual edits on the canvas that must be reflected back in Python code
 * - US3 introduces canvas interactions (drag, rename, connect, delete) which
 *   are the first features that need canvas → code generation
 */

import type { GraphModel, DiagramNode, DiagramEdge, DiagramCluster } from "@/types/diagram";

/**
 * Convert a graph model back to valid diagrams API Python code.
 * Generates import statements, Diagram context, Cluster contexts, node
 * declarations, and edge statements using the >> / << / - operators.
 */
export function generateDiagramCode(
  model: GraphModel,
  diagramName: string = "Architecture",
  direction: string = "LR",
  theme: string = "neutral",
): string {
  const lines: string[] = [];

  // Collect imports by provider.category
  const importMap = new Map<string, Set<string>>();
  for (const node of model.nodes) {
    if (node.provider === "custom") {
      importMap.set("diagrams.custom", (importMap.get("diagrams.custom") || new Set()).add("Custom"));
    } else {
      const key = `diagrams.${node.provider}.${node.category}`;
      const existing = importMap.get(key) || new Set();
      existing.add(node.service);
      importMap.set(key, existing);
    }
  }

  // Generate import statements
  lines.push("from diagrams import Diagram, Cluster, Edge");
  for (const [module, classes] of [...importMap.entries()].sort()) {
    const sorted = [...classes].sort();
    lines.push(`from ${module} import ${sorted.join(", ")}`);
  }
  lines.push("");

  // Diagram context
  lines.push(
    `with Diagram("${diagramName}", show=False, direction="${direction}", theme="${theme}"):`,
  );

  // Build cluster hierarchy
  const topLevelClusters = model.clusters.filter((c) => !c.parentClusterId);
  const topLevelNodes = model.nodes.filter((n) => !n.clusterId);

  // Render clusters recursively
  function renderCluster(cluster: DiagramCluster, indent: number): void {
    const pad = "    ".repeat(indent);
    lines.push(`${pad}with Cluster("${cluster.label}"):`);

    // Nodes in this cluster
    const clusterNodes = model.nodes.filter((n) => n.clusterId === cluster.id);
    for (const node of clusterNodes) {
      renderNode(node, indent + 1);
    }

    // Child clusters
    const children = model.clusters.filter(
      (c) => c.parentClusterId === cluster.id,
    );
    for (const child of children) {
      renderCluster(child, indent + 1);
    }

    // Empty cluster guard
    if (clusterNodes.length === 0 && children.length === 0) {
      lines.push(`${pad}    pass`);
    }
  }

  function renderNode(node: DiagramNode, indent: number): void {
    const pad = "    ".repeat(indent);
    const label = node.label || node.service;
    if (node.provider === "custom") {
      lines.push(`${pad}${node.id} = Custom("${label}", "${node.iconPath}")`);
    } else {
      lines.push(`${pad}${node.id} = ${node.service}("${label}")`);
    }
  }

  // Render top-level clusters
  for (const cluster of topLevelClusters) {
    renderCluster(cluster, 1);
  }

  // Render top-level nodes
  for (const node of topLevelNodes) {
    renderNode(node, 1);
  }

  // Render edges
  if (model.edges.length > 0) {
    lines.push("");
    for (const edge of model.edges) {
      const pad = "    ";
      const op =
        edge.direction === "forward"
          ? ">>"
          : edge.direction === "reverse"
            ? "<<"
            : "-";
      lines.push(`${pad}${edge.sourceNodeId} ${op} ${edge.targetNodeId}`);
    }
  }

  lines.push("");
  return lines.join("\n");
}
