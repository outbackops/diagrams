# WebSocket Protocol: Diagram Agent Live Sync

**Feature**: `001-ai-diagram-agent`  
**Date**: 2026-02-18  
**Endpoint**: `ws://{host}/api/v1/ws/{diagramId}`

## Overview

The WebSocket connection enables real-time bidirectional synchronization between the code editor, visual canvas, and backend rendering engine. It replaces polling for live preview updates and enables sub-second sync between code and canvas.

## Connection Lifecycle

```
Client                                 Server
  │                                      │
  ├─── CONNECT ws://.../ws/{diagramId} ──►│
  │                                      │
  │◄── session.init ─────────────────────┤   (server sends current state)
  │                                      │
  │─── code.update ─────────────────────►│   (user edits code)
  │◄── render.result ────────────────────┤   (server returns rendered layout)
  │                                      │
  │─── canvas.update ───────────────────►│   (user drags node on canvas)
  │◄── code.sync ───────────────────────┤   (server returns updated code)
  │                                      │
  │─── ping ────────────────────────────►│   (keepalive every 30s)
  │◄── pong ─────────────────────────────┤
  │                                      │
  │─── DISCONNECT ──────────────────────►│
```

## Message Format

All messages are JSON with a `type` field and corresponding `payload`.

```json
{
  "type": "<message_type>",
  "id": "<optional_correlation_id>",
  "payload": { ... }
}
```

## Client → Server Messages

### `code.update`

Sent when the user modifies code in the editor. Debounced (recommended: 500ms).

```json
{
  "type": "code.update",
  "id": "msg-001",
  "payload": {
    "source_code": "from diagrams import Diagram\n...",
    "cursor_position": { "line": 5, "column": 12 }
  }
}
```

**Server responds with**: `render.result` (if code is valid) or `validation.error` (if code has errors).

### `canvas.update`

Sent when the user modifies the diagram on the visual canvas.

```json
{
  "type": "canvas.update",
  "id": "msg-002",
  "payload": {
    "action": "move_node",
    "node_id": "abc123",
    "position": { "x": 150.0, "y": 300.0 }
  }
}
```

**Supported actions**:

| Action | Payload Fields | Description |
|--------|---------------|-------------|
| `move_node` | `node_id`, `position: {x, y}` | User dragged a node |
| `rename_node` | `node_id`, `label: string` | User renamed a node label |
| `add_edge` | `source_id`, `target_id`, `direction: "forward"\|"reverse"\|"both"` | User drew a connection |
| `remove_edge` | `edge_id` | User deleted an edge |
| `remove_node` | `node_id` | User deleted a node (and its edges) |
| `add_node` | `provider`, `category`, `service`, `label`, `cluster_id?` | User added a node from palette |
| `create_cluster` | `label`, `node_ids: string[]`, `parent_cluster_id?` | User grouped nodes into cluster |
| `remove_cluster` | `cluster_id` | User ungrouped a cluster |

**Server responds with**: `code.sync` (updated Python code reflecting the canvas change).

### `autosave.request`

Sent periodically (default: every 30s) or on demand.

```json
{
  "type": "autosave.request",
  "id": "msg-003",
  "payload": {
    "source_code": "...",
    "layout_metadata": { ... }
  }
}
```

**Server responds with**: `autosave.ack`.

### `ping`

Keepalive.

```json
{ "type": "ping" }
```

## Server → Client Messages

### `session.init`

Sent immediately after connection. Contains the current diagram state.

```json
{
  "type": "session.init",
  "payload": {
    "diagram_id": "uuid",
    "source_code": "from diagrams import Diagram\n...",
    "layout_metadata": { ... },
    "graph_model": {
      "nodes": [...],
      "edges": [...],
      "clusters": [...]
    },
    "rendered_svg": "<svg>...</svg>"
  }
}
```

### `render.result`

Sent after successful code validation and rendering.

```json
{
  "type": "render.result",
  "id": "msg-001",
  "payload": {
    "graph_model": {
      "nodes": [
        {
          "id": "node_abc",
          "provider": "aws",
          "category": "compute",
          "service": "EC2",
          "label": "Web Server",
          "icon_path": "resources/aws/compute/ec2.png",
          "position": { "x": 100, "y": 200 }
        }
      ],
      "edges": [
        {
          "id": "edge_001",
          "source_node_id": "node_abc",
          "target_node_id": "node_def",
          "direction": "forward",
          "label": null
        }
      ],
      "clusters": [
        {
          "id": "cluster_vpc",
          "label": "VPC",
          "depth": 0,
          "node_ids": ["node_abc", "node_def"],
          "child_cluster_ids": []
        }
      ]
    },
    "dot_source": "digraph { ... }",
    "render_time_ms": 250
  }
}
```

### `code.sync`

Sent after a canvas update. Contains the updated Python source code.

```json
{
  "type": "code.sync",
  "id": "msg-002",
  "payload": {
    "source_code": "from diagrams import Diagram\n...",
    "change_description": "Added edge from Web Server to Database",
    "affected_lines": [8, 9]
  }
}
```

### `validation.error`

Sent when submitted code has errors.

```json
{
  "type": "validation.error",
  "id": "msg-001",
  "payload": {
    "errors": [
      {
        "line": 5,
        "column": 12,
        "message": "NameError: name 'EC3' is not defined. Did you mean 'EC2'?",
        "severity": "error"
      }
    ]
  }
}
```

### `autosave.ack`

Confirms autosave success.

```json
{
  "type": "autosave.ack",
  "id": "msg-003",
  "payload": {
    "version": 5,
    "saved_at": "2026-02-18T10:30:00Z"
  }
}
```

### `pong`

Response to keepalive.

```json
{ "type": "pong" }
```

### `error`

Generic error message.

```json
{
  "type": "error",
  "id": "msg-001",
  "payload": {
    "code": "EXECUTION_TIMEOUT",
    "message": "Diagram rendering exceeded 30 second timeout",
    "recoverable": true
  }
}
```

## Error Codes

| Code | Description | Recoverable |
|------|-------------|-------------|
| `INVALID_CODE` | Python code has syntax errors | Yes — fix and resend |
| `UNSAFE_CODE` | Code failed AST safety validation | Yes — remove unsafe imports |
| `EXECUTION_TIMEOUT` | Rendering exceeded 30s limit | Yes — simplify diagram |
| `EXECUTION_ERROR` | Runtime error during diagram execution | Yes — fix code |
| `NODE_NOT_FOUND` | Referenced node class doesn't exist | Yes — use valid node |
| `SESSION_EXPIRED` | WebSocket session timed out | Reconnect required |
| `INTERNAL_ERROR` | Unexpected server error | Retry |

## Rate Limiting

- `code.update`: Clients should debounce at 500ms minimum. Server accepts max 10 updates/second per session.
- `canvas.update`: No debounce needed for single actions. Batch rapid drag events into a single `move_node` on drag-end.
- `autosave.request`: Max once per 10 seconds.
