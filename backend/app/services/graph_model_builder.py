"""Graph model builder — parse diagram Python code and build a graph model
with accurate icon paths from the node registry.

This runs server-side so we can use the actual diagrams library introspection
to get correct icon paths, instead of guessing on the frontend.
"""

from __future__ import annotations

import ast
import re
from typing import Any

from app.services.node_registry import node_registry


def build_graph_model(source_code: str) -> dict[str, Any]:
    """Parse diagram Python source code and return a graph model with
    accurate node data including icon paths from the registry."""

    nodes: list[dict] = []
    edges: list[dict] = []
    clusters: list[dict] = []

    # Parse imports to map class names to providers
    import_map: dict[str, dict] = {}
    for match in re.finditer(
        r"from\s+(diagrams\.(\w+)\.(\w+))\s+import\s+(.+)", source_code
    ):
        module, provider, category, classes_str = (
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
        )
        for cls in classes_str.split(","):
            cls = cls.strip()
            if cls:
                # Look up in node registry for accurate icon path
                registry_matches = [
                    n
                    for n in node_registry.get_nodes_for_provider(provider)
                    if n.class_name == cls
                ]
                icon_path = ""
                if registry_matches:
                    icon_path = registry_matches[0].icon_path
                else:
                    # Fallback: construct from convention
                    icon_path = f"resources/{provider}/{category}/{_to_icon_name(cls)}.png"

                import_map[cls] = {
                    "provider": provider,
                    "category": category,
                    "module": module,
                    "icon_path": icon_path,
                }

    # Parse node declarations: var = ClassName("label")
    node_vars: dict[str, dict] = {}
    for match in re.finditer(
        r'^\s*(\w+)\s*=\s*(\w+)\(\s*"([^"]*)"', source_code, re.MULTILINE
    ):
        var_name, class_name, label = match.group(1), match.group(2), match.group(3)
        if class_name in import_map:
            info = import_map[class_name]
            node = {
                "id": var_name,
                "provider": info["provider"],
                "category": info["category"],
                "service": class_name,
                "label": label or class_name,
                "iconPath": info["icon_path"],
                "clusterId": None,
                "position": {"x": 0, "y": 0},
            }
            nodes.append(node)
            node_vars[var_name] = node

    # Parse edges: handle chained expressions like a >> b >> c and list targets [a, b]
    edge_idx = 0
    for line in source_code.split("\n"):
        stripped = line.strip()
        # Skip empty, comments, imports, with-statements, and assignments
        if not stripped or stripped.startswith("#") or stripped.startswith("from ") or stripped.startswith("import "):
            continue
        if stripped.startswith("with "):
            continue
        # Only process lines that contain edge operators AND don't have = before the first >>/<</- 
        if ">>" not in stripped and "<<" not in stripped and " - " not in stripped:
            continue
        # Skip node declaration lines: var = ClassName(...)
        if re.match(r'^\w+\s*=\s*\w+\(', stripped):
            continue

        # Split by >> or << operators (but not -)
        parts = re.split(r'\s*(>>|<<)\s*', stripped)
        prev_nodes: list[str] = []
        prev_op = ">>"
        for part in parts:
            part = part.strip()
            if part in (">>", "<<"):
                prev_op = part
                continue
            # Part could be a single var or [list]
            if part.startswith("[") and part.endswith("]"):
                inner = part[1:-1]
                current_nodes = [v.strip() for v in inner.split(",") if v.strip()]
            else:
                # Clean trailing comments or semicolons
                varname = re.match(r'^(\w+)', part)
                current_nodes = [varname.group(1)] if varname else []

            if prev_nodes and current_nodes:
                direction = "forward" if prev_op == ">>" else "reverse" if prev_op == "<<" else "none"
                for src in prev_nodes:
                    for tgt in current_nodes:
                        if src in node_vars and tgt in node_vars:
                            edges.append({
                                "id": f"edge_{edge_idx}",
                                "sourceNodeId": src,
                                "targetNodeId": tgt,
                                "direction": direction,
                                "label": None,
                                "style": None,
                                "color": None,
                            })
                            edge_idx += 1

            if current_nodes:
                prev_nodes = current_nodes

    # Also parse standalone - edges: a - b (bidirectional)
    for match in re.finditer(r'^[ \t]+(\w+)\s+-\s+(\w+)\s*$', source_code, re.MULTILINE):
        src, tgt = match.group(1), match.group(2)
        if src in node_vars and tgt in node_vars:
            edges.append({
                "id": f"edge_{edge_idx}",
                "sourceNodeId": src,
                "targetNodeId": tgt,
                "direction": "none",
                "label": None,
                "style": None,
                "color": None,
            })
            edge_idx += 1

    # Parse clusters: with Cluster("label"):
    cluster_idx = 0
    for match in re.finditer(
        r'with\s+Cluster\(\s*"([^"]*)"', source_code
    ):
        label = match.group(1)
        clusters.append({
            "id": f"cluster_{cluster_idx}",
            "label": label,
            "parentClusterId": None,
            "depth": 0,
            "nodeIds": [],
            "childClusterIds": [],
        })
        cluster_idx += 1

    # Auto-layout: use topological ordering for data-flow layout
    # Build adjacency for a left-to-right flow
    in_degree: dict[str, int] = {n["id"]: 0 for n in nodes}
    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        src, tgt = e["sourceNodeId"], e["targetNodeId"]
        if src in adj and tgt in in_degree:
            adj[src].append(tgt)
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    # Topological sort (Kahn's algorithm)
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    layers: list[list[str]] = []
    visited = set()
    while queue:
        layers.append(list(queue))
        next_queue = []
        for nid in queue:
            visited.add(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor not in visited:
                    next_queue.append(neighbor)
        queue = next_queue

    # Add any unvisited nodes (disconnected)
    remaining = [n["id"] for n in nodes if n["id"] not in visited]
    if remaining:
        layers.append(remaining)

    # Position nodes: layers flow left-to-right, nodes in each layer stack vertically
    x_spacing = 300
    y_spacing = 180
    total_height = max(len(layer) for layer in layers) * y_spacing if layers else 0
    for layer_idx, layer in enumerate(layers):
        layer_height = len(layer) * y_spacing
        y_start = (total_height - layer_height) / 2 + 100
        for node_idx, nid in enumerate(layer):
            for node in nodes:
                if node["id"] == nid:
                    node["position"] = {
                        "x": layer_idx * x_spacing + 100,
                        "y": y_start + node_idx * y_spacing,
                    }
                    break

    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
    }


def _to_icon_name(class_name: str) -> str:
    """Convert CamelCase class name to kebab-case icon filename.
    E.g., APIGateway -> api-gateway, ElasticLoadBalancing -> elastic-load-balancing
    """
    # Insert hyphen before uppercase letters that follow lowercase
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", class_name)
    # Insert hyphen between consecutive uppercase and following lowercase
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", s)
    return s.lower()
