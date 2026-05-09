import { ChangeEvent, FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { FileUp, Library, LogOut, MessageSquare, Plus, RefreshCw, Trash2, UploadCloud } from "lucide-react";

import {
  createKnowledgeBase,
  deleteDocument,
  DocumentRead,
  DocumentUploadResult,
  KnowledgeBase,
  listDocuments,
  listKnowledgeBases,
  uploadDocument,
} from "../api/client";
import { useAuth } from "../state/auth";
import { QaPage } from "./QaPage";

type CreateFormState = {
  name: string;
  description: string;
  visibility: KnowledgeBase["visibility"];
};

const emptyForm: CreateFormState = {
  name: "",
  description: "",
  visibility: "private",
};

const ALLOWED_ACCEPT = ".txt,.pdf,.docx,.xlsx,.pptx,.md,text/plain,text/markdown,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.openxmlformats-officedocument.presentationml.presentation";

export function KnowledgeBasePage() {
  const auth = useAuth();
  const [tab, setTab] = useState<"manage" | "qa">("manage");
  const [items, setItems] = useState<KnowledgeBase[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [form, setForm] = useState<CreateFormState>(emptyForm);
  const [file, setFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResult | null>(null);
  const [documents, setDocuments] = useState<DocumentRead[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);
  const [deletingId, setDeletingId] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState("");

  const selected = useMemo(
    () => items.find((item) => item.id === selectedId) ?? items[0],
    [items, selectedId],
  );

  const selectedKbIds = useMemo(() => {
    return selected ? [selected.id] : [];
  }, [selected]);

  const selectedKbNames = useMemo(() => {
    return selected ? [selected.name] : [];
  }, [selected]);

  async function loadKnowledgeBases() {
    setLoading(true);
    setMessage("");
    try {
      const data = await listKnowledgeBases();
      setItems(data);
      if (!selectedId && data[0]) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "加载知识库失败");
    } finally {
      setLoading(false);
    }
  }

  const loadDocumentsList = useCallback(async () => {
    if (!selected) return;
    setDocsLoading(true);
    try {
      const data = await listDocuments(selected.id);
      setDocuments(data);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "加载文档列表失败");
    } finally {
      setDocsLoading(false);
    }
  }, [selected]);

  useEffect(() => {
    void loadKnowledgeBases();
  }, []);

  useEffect(() => {
    if (selected) {
      void loadDocumentsList();
    } else {
      setDocuments([]);
    }
  }, [selected, loadDocumentsList]);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    try {
      const created = await createKnowledgeBase({
        name: form.name.trim(),
        description: form.description.trim() || undefined,
        visibility: form.visibility,
      });
      setItems((current) => [created, ...current]);
      setSelectedId(created.id);
      setForm(emptyForm);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "创建知识库失败");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || !file) {
      setMessage("请选择知识库和文件");
      return;
    }
    setSubmitting(true);
    setMessage("");
    try {
      const result = await uploadDocument(selected.id, file);
      setUploadResult(result);
      setFile(null);
      void loadDocumentsList();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "上传失败");
    } finally {
      setSubmitting(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
  }

  async function handleDelete(documentId: string) {
    if (!selected || !window.confirm("确认删除该文档？")) return;
    setDeletingId(documentId);
    try {
      await deleteDocument(selected.id, documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "删除失败");
    } finally {
      setDeletingId("");
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <Library size={22} />
          <span>知识库管理台</span>
        </div>
        <nav className="sidebar-nav">
          <button
            className={tab === "manage" ? "nav-item active" : "nav-item"}
            onClick={() => setTab("manage")}
          >
            <Library size={18} /> 知识库
          </button>
          <button
            className={tab === "qa" ? "nav-item active" : "nav-item"}
            onClick={() => setTab("qa")}
          >
            <MessageSquare size={18} /> 问答
          </button>
        </nav>
        <button className="ghost-button" onClick={auth.logout} type="button">
          <LogOut size={18} />
          退出
        </button>
      </aside>

      {tab === "qa" ? (
        <main className="workspace">
          <QaPage knowledgeBaseIds={selectedKbIds} knowledgeBaseNames={selectedKbNames} />
        </main>
      ) : (
        <main className="workspace">
          <header className="workspace-header">
            <div>
              <h1>知识库</h1>
              <p>管理可访问知识库，并上传文档进入解析流程。</p>
            </div>
            <button className="secondary-button" onClick={loadKnowledgeBases} type="button">
              <RefreshCw size={17} />
              {loading ? "刷新中" : "刷新"}
            </button>
          </header>

          {message ? <div className="error-banner">{message}</div> : null}

          <section className="content-grid">
            <section className="panel">
              <div className="panel-title">
                <h2>知识库列表</h2>
                <span>{items.length}</span>
              </div>
              <div className="kb-list">
                {items.map((item) => (
                  <button
                    className={item.id === selected?.id ? "kb-item active" : "kb-item"}
                    key={item.id}
                    onClick={() => setSelectedId(item.id)}
                    type="button"
                  >
                    <strong>{item.name}</strong>
                    <span>{item.visibility}</span>
                  </button>
                ))}
                {!items.length && !loading ? <p className="muted">暂无知识库</p> : null}
              </div>
            </section>

            <section className="panel">
              <div className="panel-title">
                <h2>创建知识库</h2>
                <Plus size={18} />
              </div>
              <form className="stack-form" onSubmit={handleCreate}>
                <label>
                  名称
                  <input
                    value={form.name}
                    onChange={(event) => setForm({ ...form, name: event.target.value })}
                    placeholder="例如：产品制度库"
                    required
                  />
                </label>
                <label>
                  描述
                  <textarea
                    value={form.description}
                    onChange={(event) => setForm({ ...form, description: event.target.value })}
                    placeholder="知识库用途"
                    rows={3}
                  />
                </label>
                <label>
                  可见性
                  <select
                    value={form.visibility}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        visibility: event.target.value as KnowledgeBase["visibility"],
                      })
                    }
                  >
                    <option value="private">private</option>
                    <option value="department">department</option>
                    <option value="company">company</option>
                  </select>
                </label>
                <button className="primary-button" disabled={submitting} type="submit">
                  <Plus size={18} />
                  创建
                </button>
              </form>
            </section>

            <section className="panel wide-panel">
              <div className="panel-title">
                <h2>文档上传</h2>
                <FileUp size={18} />
              </div>
              {selected ? (
                <div className="detail-layout">
                  <div className="kb-summary">
                    <h3>{selected.name}</h3>
                    <p>{selected.description || "暂无描述"}</p>
                    <dl>
                      <dt>ID</dt>
                      <dd>{selected.id}</dd>
                      <dt>可见性</dt>
                      <dd>{selected.visibility}</dd>
                    </dl>
                  </div>
                  <form className="upload-form" onSubmit={handleUpload}>
                    <label className="file-drop">
                      <UploadCloud size={26} />
                      <span>{file ? file.name : "选择文档文件"}</span>
                      <input accept={ALLOWED_ACCEPT} onChange={handleFileChange} type="file" />
                    </label>
                    <button className="primary-button" disabled={submitting || !file} type="submit">
                      <UploadCloud size={18} />
                      上传
                    </button>
                  </form>
                </div>
              ) : (
                <p className="muted">请先创建或选择知识库</p>
              )}

              {uploadResult ? (
                <div className="result-box">
                  <strong>上传成功</strong>
                  <span>document_id: {uploadResult.document_id}</span>
                  <span>version_id: {uploadResult.version_id}</span>
                  <span>version: {uploadResult.version_number}</span>
                  <span>status: {uploadResult.status}</span>
                  <span>storage_path: {uploadResult.storage_path}</span>
                </div>
              ) : null}
            </section>

            <section className="panel wide-panel">
              <div className="panel-title">
                <h2>文档列表</h2>
                <span>{documents.length}</span>
              </div>
              {selected ? (
                docsLoading ? (
                  <p className="muted">加载中...</p>
                ) : documents.length === 0 ? (
                  <p className="muted">暂无文档，请上传</p>
                ) : (
                  <div className="doc-table">
                    <table>
                      <thead>
                        <tr>
                          <th>文档名</th>
                          <th>版本</th>
                          <th>状态</th>
                          <th>上传时间</th>
                          <th>操作</th>
                        </tr>
                      </thead>
                      <tbody>
                        {documents.map((doc) => (
                          <tr key={doc.id}>
                            <td className="doc-name">{doc.title}</td>
                            <td>v{doc.current_version?.version_number ?? "-"}</td>
                            <td>
                              <span className={`doc-status doc-status--${doc.current_version?.status ?? "unknown"}`}>
                                {doc.current_version?.status ?? doc.status}
                              </span>
                            </td>
                            <td className="doc-time">
                              {doc.current_version?.created_at
                                ? new Date(doc.current_version.created_at).toLocaleString("zh-CN")
                                : "-"}
                            </td>
                            <td>
                              <button
                                className="doc-delete-btn"
                                onClick={() => handleDelete(doc.id)}
                                disabled={deletingId === doc.id}
                                title="删除文档"
                              >
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              ) : (
                <p className="muted">请先选择知识库</p>
              )}
            </section>
          </section>
        </main>
      )}
    </div>
  );
}
