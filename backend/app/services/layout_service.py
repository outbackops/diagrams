"""Layout sidecar service — read/write LayoutMetadata JSON, merge pinned positions.

Layout metadata is stored separately from diagram source code per Constitution III
and FR-007. Drag positions are never injected into the Python code.
"""

from __future__ import annotations

from app.models.diagram import LayoutMetadata


def create_default_layout() -> LayoutMetadata:
    """Create a default empty layout metadata."""
    return LayoutMetadata()


def merge_node_position(
    layout: LayoutMetadata, node_id: str, x: float, y: float, pinned: bool = True
) -> LayoutMetadata:
    """Update or add a node position in the layout metadata."""
    layout.node_positions[node_id] = {"x": x, "y": y, "pinned": pinned}
    return layout


def merge_cluster_bounds(
    layout: LayoutMetadata,
    cluster_id: str,
    x: float,
    y: float,
    width: float,
    height: float,
) -> LayoutMetadata:
    """Update or add cluster bounds in the layout metadata."""
    layout.cluster_bounds[cluster_id] = {
        "x": x, "y": y, "width": width, "height": height
    }
    return layout


def update_viewport(
    layout: LayoutMetadata, zoom: float, pan_x: float, pan_y: float
) -> LayoutMetadata:
    """Update viewport zoom and pan."""
    layout.viewport = {"zoom": zoom, "pan_x": pan_x, "pan_y": pan_y}
    return layout


def remove_node_position(layout: LayoutMetadata, node_id: str) -> LayoutMetadata:
    """Remove a node position when a node is deleted."""
    layout.node_positions.pop(node_id, None)
    return layout


def remove_cluster_bounds(layout: LayoutMetadata, cluster_id: str) -> LayoutMetadata:
    """Remove cluster bounds when a cluster is deleted."""
    layout.cluster_bounds.pop(cluster_id, None)
    return layout
