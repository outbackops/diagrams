/**
 * Graphviz WASM layout service — load @hpcc-js/wasm-graphviz, compute layout
 * from DOT string, extract node positions.
 *
 * Graphviz is used ONLY for layout computation, not rendering.
 * React Flow handles all rendering and interaction.
 */

import { Graphviz } from "@hpcc-js/wasm-graphviz";
import type { Position } from "@/types/diagram";

let graphvizInstance: Graphviz | null = null;

async function getGraphviz(): Promise<Graphviz> {
  if (!graphvizInstance) {
    graphvizInstance = await Graphviz.load();
  }
  return graphvizInstance;
}

export interface LayoutResult {
  nodePositions: Record<string, Position>;
  clusterBounds: Record<
    string,
    { x: number; y: number; width: number; height: number }
  >;
}

/**
 * Compute layout positions from a DOT string using @hpcc-js/wasm.
 * Returns JSON output with node positions and cluster bounding boxes.
 */
export async function computeLayout(dotString: string): Promise<LayoutResult> {
  const gv = await getGraphviz();
  const result: LayoutResult = { nodePositions: {}, clusterBounds: {} };

  try {
    // Use JSON output format to get structured layout data
    const jsonOutput = gv.layout(dotString, "json", "dot");
    const parsed = JSON.parse(jsonOutput);

    // Extract node positions
    if (parsed.objects) {
      for (const obj of parsed.objects) {
        if (obj.pos) {
          const [x, y] = obj.pos.split(",").map(Number);
          // Use the node name as ID (strip quotes if present)
          const nodeId = (obj.name || "").replace(/"/g, "");
          if (nodeId && !isNaN(x) && !isNaN(y)) {
            result.nodePositions[nodeId] = { x, y: -y }; // Graphviz Y is inverted
          }
        }

        // Extract subgraph/cluster bounds
        if (obj.bb && obj.name?.startsWith("cluster_")) {
          const [x1, y1, x2, y2] = obj.bb.split(",").map(Number);
          const clusterId = obj.name;
          result.clusterBounds[clusterId] = {
            x: x1,
            y: -y2, // Graphviz Y is inverted
            width: x2 - x1,
            height: y2 - y1,
          };
        }
      }
    }

    // Also try edges array for edge positions (not used yet but available)
  } catch {
    // If JSON parsing fails, try SVG fallback for basic positions
    console.warn("Graphviz JSON layout failed, positions may be approximate");
  }

  return result;
}

/**
 * Render DOT string to SVG for preview purposes.
 */
export async function renderToSvg(dotString: string): Promise<string> {
  const gv = await getGraphviz();
  return gv.layout(dotString, "svg", "dot");
}
