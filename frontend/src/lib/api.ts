export type ApiResponse<T> = {
  success: boolean;
  data: T;
  warnings?: string[];
  errors?: string[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function clearAuthToken() {
  authToken = null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
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
};

export type Project = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  owner_id?: string | null;
  status: string;
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
};

export type ExecutionArtifact = {
  id: string;
  execution_id: string;
  artifact_type: string;
  name: string;
  storage_uri: string;
};

export type ExecutionTimelineEntry = {
  stage: string;
  status: string;
  message: string;
};

export type ReportSummary = {
  execution_id: string;
  summary: Record<string, unknown>;
  artifacts: Array<Record<string, unknown>>;
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
};

export type AiResult = {
  model: string;
  confidence: number;
  result: Record<string, unknown>;
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

export type Settings = {
  app_name: string;
  app_version: string;
  log_level: string;
  database_url: string;
  redis_url: string;
};
