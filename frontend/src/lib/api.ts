export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type ApiResponse<T> = {
  success: boolean;
  data: T;
  warnings?: string[];
  errors?: string[];
};

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function clearAuthToken() {
  authToken = null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export const api = {
  get<T>(path: string) {
    return request<T>(path);
  },
  post<T>(path: string, body?: unknown) {
    return request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
  },
  put<T>(path: string, body?: unknown) {
    return request<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined });
  },
  delete<T>(path: string) {
    return request<T>(path, { method: "DELETE" });
  },
  async download(path: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
      },
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.blob();
  },
};

export type Project = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  owner_id?: string | null;
  status: string;
};

export type Asset = {
  id: string;
  project_id: string;
  asset_type: string;
  name: string;
  version?: string | null;
  source_ref?: string | null;
  metadata: Record<string, unknown>;
  status: string;
};

export type AssetRevision = {
  id: string;
  asset_id: string;
  revision_number: number;
  version?: string | null;
  snapshot: Asset;
  change_summary?: string | null;
  created_by?: string | null;
  created_at?: string | null;
};

export type AssetLink = {
  id: string;
  asset_id: string;
  ref_type: string;
  ref_id: string;
  ref_name: string;
  reason: string;
  created_at?: string | null;
};

export type AssetImpact = {
  asset: Asset;
  reference_count: number;
  reference_summary: Record<string, number>;
  references: AssetLink[];
  can_archive: boolean;
  blocking_reasons: string[];
};

export type TestSuite = {
  id: string;
  project_id: string;
  name: string;
  suite_type: string;
  source_type: string;
  source_ref: string;
  default_env_id?: string | null;
  status: string;
};

export type Environment = {
  id: string;
  project_id: string;
  name: string;
  env_type: string;
  base_url: string;
  enabled: boolean;
};

export type Execution = {
  id: string;
  project_id: string;
  suite_id: string;
  env_id: string;
  trigger_type: string;
  trigger_source?: string | null;
  request_params: Record<string, unknown>;
  status: string;
  summary: Record<string, unknown>;
  completion_source?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
};

export type ExecutionArtifact = {
  id: string;
  execution_id: string;
  artifact_type: string;
  name: string;
  storage_uri: string;
};

export type ExecutionTask = {
  id: string;
  execution_id: string;
  task_key: string;
  task_name: string;
  status: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  error_message?: string | null;
};

export type ExecutionTimelineEntry = {
  stage: string;
  status: string;
  message: string;
};

export type ExecutionDispatchResult = {
  execution_id: string;
  status: string;
  task_id: string;
  summary: Record<string, unknown>;
};

export type ReportSummary = {
  execution_id: string;
  status: string;
  summary: Record<string, unknown>;
  artifacts: Array<Record<string, unknown>>;
  tasks: Array<Record<string, unknown>>;
  task_count: number;
  completion_source?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
};

export type ReportIndexItem = ReportSummary & {
  status: string;
};

export type GateRule = {
  id: string;
  project_id: string;
  name: string;
  rule_type: string;
  enabled: boolean;
  config: Record<string, unknown>;
};

export type GateResult = {
  execution_id: string;
  result: string;
  score: number;
  reason: string;
  task_count: number;
  failed_tasks: number;
  task_threshold: number;
  completion_source?: string | null;
};

export type AiResult = {
  model: string;
  confidence: number;
  result: Record<string, unknown>;
};

export type AiHistoryItem = {
  id: string;
  execution_id: string;
  insight_type: string;
  model_name: string;
  provider_name: string;
  prompt_version: string;
  confidence: number;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown>;
  fallback_from?: string | null;
  fallback_reason?: string | null;
};

export type AuditLog = {
  id: string;
  actor_id?: string | null;
  action: string;
  target_type: string;
  target_id: string;
  request_json: Record<string, unknown>;
  response_json: Record<string, unknown>;
};

export type SettingsHistoryEntry = {
  environment: string;
  revision_number: number;
  action: string;
  app_name: string;
  app_version: string;
  log_level: string;
  jenkins_url: string;
  jenkins_user: string;
  ai_provider: string;
  ai_model_name: string;
  updated_at: string;
};

export type AuditOverview = {
  audit_log_count: number;
  gate_change_count: number;
  settings_revision_count: number;
  asset_revision_count: number;
  connector_count: number;
  connectors: ConnectorInfo[];
  recent_audit_logs: AuditLog[];
  recent_gate_changes: AuditLog[];
  recent_settings_history: SettingsHistoryEntry[];
  recent_asset_revisions: AssetRevision[];
};

export type GovernanceEventKind =
  | "asset_change"
  | "asset_block"
  | "gate_change"
  | "gate_fail"
  | "settings_update"
  | "settings_rollback"
  | "connector_status"
  | "audit_event";

export type GovernanceEventSeverity = "info" | "warn" | "error" | "blocked";

export type GovernanceEvent = {
  id: string;
  kind: GovernanceEventKind;
  source_type: string;
  source_id: string;
  timestamp: string;
  severity: GovernanceEventSeverity;
  status?: string | null;
  target_type?: string | null;
  target_id?: string | null;
  project_id?: string | null;
  environment?: string | null;
  title: string;
  description?: string | null;
  metadata: Record<string, unknown>;
};

export type GovernanceEventDetail = GovernanceEvent & {
  raw: Record<string, unknown>;
};

export type GovernanceOverview = {
  window: string;
  window_start: string;
  window_end: string;
  ai_provider: string;
  ai_model_name: string;
  ai_fallback_count: number;
  asset_block_count: number;
  gate_fail_count: number;
  settings_rollback_count: number;
  connector_error_count: number;
  recent_audit_count: number;
  recent_events: GovernanceEvent[];
};

export type Settings = {
  environment: string;
  revision_number: number;
  app_name: string;
  app_version: string;
  log_level: string;
  database_url: string;
  redis_url: string;
  jenkins_url: string;
  jenkins_user: string;
  ai_provider: string;
  ai_model_name: string;
};

export type ConnectorInfo = {
  connector_type: string;
  ok: boolean;
  status: string;
  message: string;
  details: Record<string, unknown>;
};
