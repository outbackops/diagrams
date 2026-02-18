/**
 * WebSocket client — connect to ws://.../ws/{diagramId}, handle all message
 * types per contracts/websocket.md.
 */

import type {
  WsMessage,
  WsMessageType,
  CanvasAction,
  GraphModel,
  Position,
} from "@/types/diagram";
import type { ValidationError, LayoutMetadata } from "@/types/api";

type MessageHandler = (payload: any) => void;

export class WsClient {
  private ws: WebSocket | null = null;
  private handlers = new Map<WsMessageType, MessageHandler[]>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private messageId = 0;
  private diagramId: string;
  private baseUrl: string;

  constructor(baseUrl: string = "") {
    this.baseUrl = baseUrl || `ws://${window.location.host}`;
    this.diagramId = "";
  }

  connect(diagramId: string): void {
    this.diagramId = diagramId;
    const url = `${this.baseUrl}/api/v1/ws/${diagramId}`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.startPing();
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        this.dispatch(msg.type, msg.payload);
      } catch {
        console.warn("Failed to parse WebSocket message");
      }
    };

    this.ws.onclose = () => {
      this.stopPing();
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    this.stopPing();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  on(type: WsMessageType, handler: MessageHandler): () => void {
    const list = this.handlers.get(type) || [];
    list.push(handler);
    this.handlers.set(type, list);
    return () => {
      const updated = (this.handlers.get(type) || []).filter(
        (h) => h !== handler,
      );
      this.handlers.set(type, updated);
    };
  }

  sendCodeUpdate(sourceCode: string, cursorLine?: number, cursorColumn?: number): void {
    this.send("code.update", {
      source_code: sourceCode,
      cursor_position: cursorLine
        ? { line: cursorLine, column: cursorColumn || 0 }
        : undefined,
    });
  }

  sendCanvasUpdate(action: CanvasAction): void {
    this.send("canvas.update", action);
  }

  sendAutoSave(sourceCode: string, layoutMetadata: LayoutMetadata | null): void {
    this.send("autosave.request", {
      source_code: sourceCode,
      layout_metadata: layoutMetadata,
    });
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private send(type: WsMessageType, payload: any): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    const id = `msg-${++this.messageId}`;
    this.ws.send(JSON.stringify({ type, id, payload }));
  }

  private dispatch(type: WsMessageType, payload: any): void {
    const handlers = this.handlers.get(type) || [];
    for (const handler of handlers) {
      try {
        handler(payload);
      } catch (err) {
        console.error(`WsClient handler error for ${type}:`, err);
      }
    }
  }

  private startPing(): void {
    this.pingTimer = setInterval(() => {
      this.send("ping", {});
    }, 30_000);
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.diagramId) {
        this.connect(this.diagramId);
      }
    }, 3000);
  }
}

// Singleton instance
export const wsClient = new WsClient();
