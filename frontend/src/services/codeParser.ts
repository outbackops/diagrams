/**
 * Parse diagram Python code → graph model.
 *
 * Extracts nodes, edges, and clusters from diagrams library Python source code
 * to build the frontend graph model. Uses regex-based parsing (not a full Python
 * parser) for speed — runs on every keystroke (debounced).
 */

import type {
  DiagramNode,
  DiagramEdge,
  DiagramCluster,
  GraphModel,
  EdgeDirection,
} from "@/types/diagram";

// Match: variable = ClassName("label")  or  variable = ClassName("label", ...)
const NODE_PATTERN =
  /^[ \t]*(\w+)\s*=\s*(\w+)\(\s*"([^"]*)"(?:.*?)?\)/gm;

// Match: from diagrams.provider.category import Class1, Class2
const IMPORT_PATTERN =
  /^[ \t]*from\s+(diagrams\.(\w+)\.(\w+))\s+import\s+(.+)/gm;

// Match: node1 >> node2, node1 << node2, node1 - node2
const EDGE_PATTERN =
  /^[ \t]*(\w+)\s*(>>|<<|-)\s*(\w+)/gm;

// Match: with Cluster("label"):  or  with Cluster("label", ...):
const CLUSTER_PATTERN =
  /^([ \t]*)with\s+Cluster\(\s*"([^"]*)"(?:.*?)?\)\s*(?:as\s+(\w+))?\s*:/gm;

// Match: with Diagram("name", ...):
const DIAGRAM_PATTERN =
  /with\s+Diagram\(\s*"([^"]*)"(?:.*?)?\)/;

interface ImportInfo {
  module: string;
  provider: string;
  category: string;
  classes: string[];
}

function parseImports(code: string): Map<string, ImportInfo> {
  const classToImport = new Map<string, ImportInfo>();
  let match: RegExpExecArray | null;
  const re = new RegExp(IMPORT_PATTERN.source, "gm");

  while ((match = re.exec(code)) !== null) {
    const [, module, provider, category, classesStr] = match;
    const classes = classesStr.split(",").map((c) => c.trim()).filter(Boolean);
    const info: ImportInfo = { module, provider, category, classes };
    for (const cls of classes) {
      classToImport.set(cls, info);
    }
  }

  return classToImport;
}

function parseNodes(
  code: string,
  imports: Map<string, ImportInfo>,
  clusterMap: Map<number, string>,
): DiagramNode[] {
  const nodes: DiagramNode[] = [];
  let match: RegExpExecArray | null;
  const re = new RegExp(NODE_PATTERN.source, "gm");

  while ((match = re.exec(code)) !== null) {
    const [, varName, className, label] = match;
    const importInfo = imports.get(className);
    if (!importInfo) continue; // Not a recognized node class

    // Determine cluster membership by indentation
    const lineStart = code.lastIndexOf("\n", match.index) + 1;
    const indent = match.index - lineStart;
    let clusterId: string | null = null;
    for (const [indentLevel, cId] of clusterMap) {
      if (indent > indentLevel) {
        clusterId = cId;
      }
    }

    nodes.push({
      id: varName,
      provider: importInfo.provider,
      category: importInfo.category,
      service: className,
      label: label || className,
      iconPath: `${importInfo.provider}/${importInfo.category}/${className.toLowerCase()}.png`,
      clusterId,
      position: { x: 0, y: 0 }, // Will be set by layout engine
    });
  }

  return nodes;
}

function parseEdges(code: string): DiagramEdge[] {
  const edges: DiagramEdge[] = [];
  let match: RegExpExecArray | null;
  const re = new RegExp(EDGE_PATTERN.source, "gm");
  let edgeIndex = 0;

  while ((match = re.exec(code)) !== null) {
    const [, source, operator, target] = match;
    let direction: EdgeDirection = "none";
    if (operator === ">>") direction = "forward";
    else if (operator === "<<") direction = "reverse";

    edges.push({
      id: `edge_${edgeIndex++}`,
      sourceNodeId: source,
      targetNodeId: target,
      direction,
      label: null,
      style: null,
      color: null,
    });
  }

  return edges;
}

function parseClusters(code: string): {
  clusters: DiagramCluster[];
  clusterMap: Map<number, string>;
} {
  const clusters: DiagramCluster[] = [];
  const clusterMap = new Map<number, string>();
  let match: RegExpExecArray | null;
  const re = new RegExp(CLUSTER_PATTERN.source, "gm");
  let clusterIndex = 0;

  while ((match = re.exec(code)) !== null) {
    const [, indent, label, alias] = match;
    const indentLevel = indent.length;
    const id = alias || `cluster_${clusterIndex++}`;

    // Determine parent by indentation
    let parentClusterId: string | null = null;
    let depth = 0;
    for (const [existingIndent, existingId] of clusterMap) {
      if (indentLevel > existingIndent) {
        parentClusterId = existingId;
        depth++;
      }
    }

    clusterMap.set(indentLevel, id);

    clusters.push({
      id,
      label,
      parentClusterId,
      depth: Math.min(depth, 3),
      nodeIds: [], // Filled after nodes are parsed
      childClusterIds: [],
    });
  }

  return { clusters, clusterMap };
}

/**
 * Parse diagram Python source code into a GraphModel.
 */
export function parseDiagramCode(code: string): GraphModel {
  const imports = parseImports(code);
  const { clusters, clusterMap } = parseClusters(code);
  const nodes = parseNodes(code, imports, clusterMap);
  const edges = parseEdges(code);

  // Fill cluster nodeIds
  for (const node of nodes) {
    if (node.clusterId) {
      const cluster = clusters.find((c) => c.id === node.clusterId);
      if (cluster) cluster.nodeIds.push(node.id);
    }
  }

  // Fill cluster childClusterIds
  for (const cluster of clusters) {
    if (cluster.parentClusterId) {
      const parent = clusters.find((c) => c.id === cluster.parentClusterId);
      if (parent) parent.childClusterIds.push(cluster.id);
    }
  }

  return { nodes, edges, clusters };
}
