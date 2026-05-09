const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "enterprise_rag_token";

export type LoginResponse = {
  access_token: string;
  token_type: string;
};

export type KnowledgeBase = {
  id: string;
  name: string;
  description: string | null;
  visibility: "private" | "department" | "company";
  department_id: string | null;
  is_active: boolean;
  owner_id: string;
};

export type DocumentUploadResult = {
  document_id: string;
  version_id: string;
  version_number: number;
  file_name: string;
  file_type: string;
  file_size: number;
  storage_path: string;
  status: string;
};

export type DocumentVersionRead = {
  id: string;
  version_number: number;
  file_name: string;
  file_type: string;
  file_size: number;
  status: string;
  error_message: string | null;
  created_at: string;
};

export type DocumentRead = {
  id: string;
  title: string;
  status: string;
  current_version: DocumentVersionRead | null;
};

export type QaAskResponse = {
  session_id: string;
  message: {
    id: string;
    role: "user" | "assistant";
    content: string;
    citations: Citation[];
    created_at: string;
  };
};

export type Citation = {
  document_id: string;
  document_title: string;
  chunk_id: string;
  chunk_text: string;
  relevance_score: number | null;
};

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getStoredToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (err) {
    if (err instanceof TypeError) {
      throw new Error(`无法连接后端服务，请确认 ${API_BASE_URL} 已启动并允许前端访问`);
    }
    throw err;
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const message = typeof payload.detail === "string" ? payload.detail : "请求失败";
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export type UserRead = {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
};

export async function getCurrentUser(): Promise<UserRead> {
  return request<UserRead>("/auth/me");
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}

export async function listKnowledgeBases(): Promise<KnowledgeBase[]> {
  return request<KnowledgeBase[]>("/knowledge-bases");
}

export async function createKnowledgeBase(input: {
  name: string;
  description?: string;
  visibility: KnowledgeBase["visibility"];
}): Promise<KnowledgeBase> {
  return request<KnowledgeBase>("/knowledge-bases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function uploadDocument(
  knowledgeBaseId: string,
  file: File,
): Promise<DocumentUploadResult> {
  const body = new FormData();
  body.set("file", file);
  return request<DocumentUploadResult>(`/knowledge-bases/${knowledgeBaseId}/documents`, {
    method: "POST",
    body,
  });
}

export async function askQuestion(
  question: string,
  knowledgeBaseIds: string[],
  sessionId?: string | null,
): Promise<QaAskResponse> {
  return request<QaAskResponse>("/qa/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      knowledge_base_ids: knowledgeBaseIds,
      session_id: sessionId ?? null,
    }),
  });
}

export async function listDocuments(knowledgeBaseId: string): Promise<DocumentRead[]> {
  return request<DocumentRead[]>(`/knowledge-bases/${knowledgeBaseId}/documents`);
}

export async function deleteDocument(knowledgeBaseId: string, documentId: string): Promise<void> {
  const headers = new Headers();
  const token = getStoredToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const resp = await fetch(`${API_BASE_URL}/knowledge-bases/${knowledgeBaseId}/documents/${documentId}`, {
    method: "DELETE",
    headers,
  });
  if (!resp.ok) {
    const payload = await resp.json().catch(() => ({} as Record<string, unknown>));
    throw new Error(typeof payload.detail === "string" ? payload.detail : "删除失败");
  }
}

export type KbMember = {
  id: string;
  user_id: string;
  username: string;
  email: string;
  role: "owner" | "manager" | "editor" | "viewer";
  knowledge_base_id: string;
};

export async function listMembers(kbId: string): Promise<KbMember[]> {
  return request<KbMember[]>(`/knowledge-bases/${kbId}/members`);
}

export async function addMember(kbId: string, userId: string, role: string): Promise<KbMember> {
  return request<KbMember>(`/knowledge-bases/${kbId}/members`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, role }),
  });
}

export async function removeMember(kbId: string, userId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/knowledge-bases/${kbId}/members/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${getStoredToken() ?? ""}` },
  });
}

export async function retryDocument(kbId: string, docId: string): Promise<DocumentUploadResult> {
  return request<DocumentUploadResult>(
    `/knowledge-bases/${kbId}/documents/${docId}/retry`,
    { method: "POST" },
  );
}

// ── Admin: Users ──

export async function listUsers(): Promise<UserRead[]> {
  return request<UserRead[]>("/users");
}

export async function createUser(input: { username: string; email: string; password: string }): Promise<UserRead> {
  return request<UserRead>("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function deleteUserApi(userId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/users/${userId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${getStoredToken() ?? ""}` },
  });
}

// ── Admin: Roles ──

export type RoleRead = {
  id: string;
  name: string;
  description: string | null;
};

export async function listRoles(): Promise<RoleRead[]> {
  return request<RoleRead[]>("/roles");
}

// ── Admin: Departments ──

export type DepartmentRead = {
  id: string;
  name: string;
  parent_id: string | null;
};

export async function listDepartments(): Promise<DepartmentRead[]> {
  return request<DepartmentRead[]>("/departments");
}

export async function createDepartment(input: { name: string; parent_id?: string | null }): Promise<DepartmentRead> {
  return request<DepartmentRead>("/departments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export async function deleteDepartmentApi(id: string): Promise<void> {
  await fetch(`${API_BASE_URL}/departments/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${getStoredToken() ?? ""}` },
  });
}

// ── Settings ──

export type SystemSettings = {
  llm: { endpoint: string; model: string; temperature: number; max_tokens: number; system_prompt: string };
  embedding: { endpoint: string; model: string };
  rerank: { endpoint: string; model: string; top_k: number };
  milvus: { uri: string; collection: string; dimension: number };
  object_storage: { endpoint: string; bucket: string; region: string };
  chat: { history_ttl: number };
  jwt: { algorithm: string; expire_minutes: number };
};

export async function getSettings(): Promise<SystemSettings> {
  return request<SystemSettings>("/settings");
}

export async function submitFeedbackApi(
  messageId: string,
  rating: "up" | "down",
  comment?: string,
): Promise<unknown> {
  return request<unknown>("/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message_id: messageId, rating, comment: comment ?? null }),
  });
}
