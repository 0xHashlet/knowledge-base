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
