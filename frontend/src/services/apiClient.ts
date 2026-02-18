/**
 * REST API client with fetch wrapper for all backend endpoints.
 */

import type {
  Diagram,
  DiagramSummary,
  DiagramVersion,
  CreateDiagramRequest,
  UpdateDiagramRequest,
  GeneratePromptRequest,
  RefinePromptRequest,
  PromptResponse,
  ImportRepoRequest,
  RepoScanResponse,
  ConfirmRepoImportRequest,
  ImportResponse,
  ExportRequest,
  ExportResponse,
  NodeRegistryEntry,
  ValidationResult,
  ApiError,
} from "@/types/api";

const API_BASE = "/api/v1";

class ApiClientError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const err: ApiError = await res.json();
      detail = err.detail || detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiClientError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Diagrams ──

export const apiClient = {
  // Diagrams CRUD
  listDiagrams: () => request<DiagramSummary[]>("/diagrams"),

  createDiagram: (data: CreateDiagramRequest) =>
    request<Diagram>("/diagrams", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getDiagram: (id: string) => request<Diagram>(`/diagrams/${id}`),

  updateDiagram: (id: string, data: UpdateDiagramRequest) =>
    request<Diagram>(`/diagrams/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteDiagram: (id: string) =>
    request<void>(`/diagrams/${id}`, { method: "DELETE" }),

  listDiagramVersions: (id: string) =>
    request<DiagramVersion[]>(`/diagrams/${id}/versions`),

  renderDiagram: (id: string, format: string = "svg") =>
    fetch(`${API_BASE}/diagrams/${id}/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ format }),
    }),

  // Prompts
  generateFromPrompt: (data: GeneratePromptRequest) =>
    request<PromptResponse>("/prompts/generate", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  refineWithPrompt: (data: RefinePromptRequest) =>
    request<PromptResponse>("/prompts/refine", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Import
  importIaCFile: (file: File, format: string) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("format", format);
    return fetch(`${API_BASE}/import/file`, {
      method: "POST",
      body: formData,
    }).then((res) => res.json()) as Promise<ImportResponse>;
  },

  importRepository: (data: ImportRepoRequest) =>
    request<RepoScanResponse>("/import/repository", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  confirmRepoImport: (data: ConfirmRepoImportRequest) =>
    request<ImportResponse>("/import/repository/confirm", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Export
  exportDiagram: (id: string, data: ExportRequest) =>
    request<ExportResponse>(`/export/${id}`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Registry
  listProviders: () => request<string[]>("/registry/providers"),

  listProviderNodes: (provider: string) =>
    request<NodeRegistryEntry[]>(`/registry/providers/${provider}/nodes`),

  searchNodes: (q: string) =>
    request<NodeRegistryEntry[]>(`/registry/search?q=${encodeURIComponent(q)}`),

  // Validation
  validateCode: (sourceCode: string) =>
    request<ValidationResult>("/validate", {
      method: "POST",
      body: JSON.stringify({ source_code: sourceCode }),
    }),
};
