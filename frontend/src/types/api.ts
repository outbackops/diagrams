/**
 * API request/response types matching contracts/openapi.yaml
 */

// ── Diagram ──

export interface DiagramSummary {
  id: string;
  name: string;
  providers: string[];
  version: number;
  updated_at: string;
}

export interface Diagram {
  id: string;
  name: string;
  source_code: string;
  dot_source: string | null;
  layout_metadata: LayoutMetadata | null;
  providers: string[];
  theme: DiagramTheme;
  direction: DiagramDirection;
  version: number;
  status: DiagramStatus;
  created_at: string;
  updated_at: string;
}

export type DiagramTheme = "neutral" | "pastel" | "blues" | "greens" | "orange";
export type DiagramDirection = "TB" | "BT" | "LR" | "RL";
export type DiagramStatus = "draft" | "generated" | "editing";

export interface CreateDiagramRequest {
  name: string;
  theme?: DiagramTheme;
  direction?: DiagramDirection;
}

export interface UpdateDiagramRequest {
  name?: string;
  source_code?: string;
  layout_metadata?: LayoutMetadata;
}

export interface DiagramVersion {
  id: string;
  version: number;
  change_summary: string | null;
  created_at: string;
}

export interface LayoutMetadata {
  version: number;
  engine: string;
  node_positions: Record<string, { x: number; y: number; pinned: boolean }>;
  cluster_bounds: Record<
    string,
    { x: number; y: number; width: number; height: number }
  >;
  viewport: { zoom: number; pan_x: number; pan_y: number };
}

// ── Prompts ──

export interface GeneratePromptRequest {
  prompt: string;
  providers?: string[];
  theme?: DiagramTheme;
  direction?: DiagramDirection;
}

export interface RefinePromptRequest {
  diagram_id: string;
  prompt: string;
}

export interface PromptResponse {
  diagram: Diagram;
  explanation: string;
  assumptions: string[];
  warnings: string[];
  diff: string | null;
  model_used: string;
  prompt_hash: string;
}

// ── Import ──

export interface ImportRepoRequest {
  repo_url: string;
  branch?: string;
  path_filter?: string;
}

export interface RepoScanResponse {
  files: Array<{
    path: string;
    format: IaCFormat;
    resource_count: number;
  }>;
  total_resources: number;
}

export interface ConfirmRepoImportRequest {
  repo_url: string;
  selected_files: string[];
}

export interface ImportResponse {
  diagram: Diagram;
  parsed_resources: ParsedResource[];
  unsupported_services: string[];
  explanation: string;
}

export interface ParsedResource {
  resource_type: string;
  resource_name: string;
  mapped_node: string | null;
  relationships: string[];
}

export type IaCFormat = "terraform" | "cloudformation" | "bicep" | "kubernetes";

// ── Export ──

export type ExportFormat = "png" | "svg" | "pdf" | "py" | "share";

export interface ExportRequest {
  format: ExportFormat;
}

export interface ExportResponse {
  format: string;
  download_url: string | null;
  share_url: string | null;
  content_base64: string | null;
}

// ── Registry ──

export interface NodeRegistryEntry {
  provider: string;
  category: string;
  class_name: string;
  aliases: string[];
  icon_path: string;
  module_path: string;
}

// ── Validation ──

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  node_count: number | null;
  edge_count: number | null;
  providers_used: string[] | null;
}

export interface ValidationError {
  line: number;
  column: number;
  message: string;
  severity: "error" | "warning";
}

// ── Common ──

export interface ApiError {
  detail: string;
  code?: string;
}
