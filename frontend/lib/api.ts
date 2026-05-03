export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: options.body instanceof FormData ? options.headers : { "Content-Type": "application/json", ...(options.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: response.statusText } }));
    throw new Error(error?.error?.message ?? "Request failed");
  }
  return response.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body: JSON.stringify(body ?? {}) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

export type Citation = {
  source: string;
  title: string;
  source_type?: string | null;
  document_name?: string | null;
  chunk_id?: string | null;
  file_path?: string | null;
  short_snippet?: string | null;
  relevance_score?: number | null;
  score?: number | null;
  metadata?: Record<string, unknown>;
};

export type TraceStep = {
  step: string;
  status: string;
  detail: string;
  data: Record<string, unknown>;
};

export type ChatResponse = {
  conversation_id: string;
  message_id: string;
  response: string;
  intent: string;
  confidence: string;
  citations: Citation[];
  trace: TraceStep[];
  tool_calls: Record<string, unknown>[];
  approval_required: boolean;
};
