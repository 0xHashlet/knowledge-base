import { FormEvent, useEffect, useState } from "react";
import { Building2, Cpu, Plus, Shield, Trash2, Users } from "lucide-react";
import {
  createDepartment,
  createUser,
  deleteDepartmentApi,
  deleteUserApi,
  DepartmentRead,
  getSettings,
  listDepartments,
  listRoles,
  listUsers,
  RoleRead,
  SystemSettings,
  UserRead,
} from "../api/client";

export function AdminPage() {
  const [tab, setTab] = useState<"users" | "roles" | "departments" | "settings">("users");
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [users, setUsers] = useState<UserRead[]>([]);
  const [roles, setRoles] = useState<RoleRead[]>([]);
  const [departments, setDepartments] = useState<DepartmentRead[]>([]);
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // ── User form
  const [userForm, setUserForm] = useState({ username: "", email: "", password: "" });

  // ── Department form
  const [deptForm, setDeptForm] = useState({ name: "", parent_id: "" });

  useEffect(() => { void loadData(); }, [tab]);

  async function loadData() {
    setMessage("");
    try {
      if (tab === "users") setUsers(await listUsers());
      else if (tab === "roles") setRoles(await listRoles());
      else if (tab === "departments") setDepartments(await listDepartments());
      else setSettings(await getSettings());
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "加载失败");
    }
  }

  async function handleCreateUser(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createUser(userForm);
      setUserForm({ username: "", email: "", password: "" });
      await loadData();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "创建用户失败");
    } finally { setSubmitting(false); }
  }

  async function handleDeleteUser(id: string) {
    if (!window.confirm("确认删除该用户？")) return;
    try { await deleteUserApi(id); setUsers((p) => p.filter((u) => u.id !== id)); }
    catch (err) { setMessage(err instanceof Error ? err.message : "删除失败"); }
  }

  async function handleCreateDept(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createDepartment({ name: deptForm.name, parent_id: deptForm.parent_id || null });
      setDeptForm({ name: "", parent_id: "" });
      await loadData();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "创建部门失败");
    } finally { setSubmitting(false); }
  }

  async function handleDeleteDept(id: string) {
    if (!window.confirm("确认删除该部门？")) return;
    try { await deleteDepartmentApi(id); setDepartments((p) => p.filter((d) => d.id !== id)); }
    catch (err) { setMessage(err instanceof Error ? err.message : "删除失败"); }
  }

  return (
    <div className="admin-page">
      <div className="admin-tabs">
        <button className={tab === "users" ? "admin-tab active" : "admin-tab"} onClick={() => setTab("users")}>
          <Users size={16} /> 用户管理
        </button>
        <button className={tab === "roles" ? "admin-tab active" : "admin-tab"} onClick={() => setTab("roles")}>
          <Shield size={16} /> 角色管理
        </button>
        <button className={tab === "departments" ? "admin-tab active" : "admin-tab"} onClick={() => setTab("departments")}>
          <Building2 size={16} /> 部门管理
        </button>
        <button className={tab === "settings" ? "admin-tab active" : "admin-tab"} onClick={() => setTab("settings")}>
          <Cpu size={16} /> 系统设置
        </button>
      </div>

      {message ? <div className="error-banner" style={{ margin: "12px 0" }}>{message}</div> : null}

      {tab === "users" && (
        <section className="panel" style={{ marginTop: 12 }}>
          <div className="panel-title"><h2>用户列表</h2><span>{users.length}</span></div>
          <form className="member-form" onSubmit={handleCreateUser} style={{ marginBottom: 14 }}>
            <input value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} placeholder="用户名" required />
            <input value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} placeholder="邮箱" type="email" required />
            <input value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} placeholder="密码" type="password" required />
            <button className="primary-button" disabled={submitting} type="submit"><Plus size={14} />创建</button>
          </form>
          <div className="doc-table">
            <table>
              <thead><tr><th>用户名</th><th>邮箱</th><th>管理员</th><th>状态</th><th>操作</th></tr></thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td><strong>{u.username}</strong></td>
                    <td>{u.email}</td>
                    <td>{u.is_superuser ? "是" : "否"}</td>
                    <td><span className={`doc-status ${u.is_active ? "doc-status--ready" : "doc-status--failed"}`}>{u.is_active ? "正常" : "禁用"}</span></td>
                    <td>
                      <button className="doc-delete-btn" onClick={() => handleDeleteUser(u.id)} title="删除"><Trash2 size={14} /></button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={5} className="muted" style={{ textAlign: "center" }}>暂无用户</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === "roles" && (
        <section className="panel" style={{ marginTop: 12 }}>
          <div className="panel-title"><h2>角色列表</h2><span>{roles.length}</span></div>
          <div className="doc-table">
            <table>
              <thead><tr><th>名称</th><th>描述</th><th>ID</th></tr></thead>
              <tbody>
                {roles.map((r) => (
                  <tr key={r.id}>
                    <td><strong>{r.name}</strong></td>
                    <td>{r.description || "-"}</td>
                    <td className="muted" style={{ fontSize: "0.78rem" }}>{r.id}</td>
                  </tr>
                ))}
                {roles.length === 0 && (
                  <tr><td colSpan={3} className="muted" style={{ textAlign: "center" }}>暂无角色</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === "departments" && (
        <section className="panel" style={{ marginTop: 12 }}>
          <div className="panel-title"><h2>部门列表</h2><span>{departments.length}</span></div>
          <form className="member-form" onSubmit={handleCreateDept} style={{ marginBottom: 14 }}>
            <input value={deptForm.name} onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} placeholder="部门名称" required />
            <input value={deptForm.parent_id} onChange={(e) => setDeptForm({ ...deptForm, parent_id: e.target.value })} placeholder="上级部门 ID (可选)" />
            <button className="primary-button" disabled={submitting} type="submit"><Plus size={14} />创建</button>
          </form>
          <div className="doc-table">
            <table>
              <thead><tr><th>名称</th><th>上级部门</th><th>ID</th><th>操作</th></tr></thead>
              <tbody>
                {departments.map((d) => (
                  <tr key={d.id}>
                    <td><strong>{d.name}</strong></td>
                    <td className="muted">{d.parent_id || "-"}</td>
                    <td className="muted" style={{ fontSize: "0.78rem" }}>{d.id}</td>
                    <td>
                      <button className="doc-delete-btn" onClick={() => handleDeleteDept(d.id)} title="删除"><Trash2 size={14} /></button>
                    </td>
                  </tr>
                ))}
                {departments.length === 0 && (
                  <tr><td colSpan={4} className="muted" style={{ textAlign: "center" }}>暂无部门</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {tab === "settings" && (
        <section className="panel" style={{ marginTop: 12 }}>
          <div className="panel-title"><h2>系统配置</h2></div>
          {settings ? (
            <div style={{ display: "grid", gap: 16, fontSize: "0.88rem" }}>
              <SettingsSection title="LLM" items={[
                ["endpoint", settings.llm.endpoint],
                ["model", settings.llm.model],
                ["temperature", String(settings.llm.temperature)],
                ["max_tokens", String(settings.llm.max_tokens)],
              ]} />
              <SettingsSection title="Embedding" items={[
                ["endpoint", settings.embedding.endpoint],
                ["model", settings.embedding.model],
              ]} />
              <SettingsSection title="Rerank" items={[
                ["endpoint", settings.rerank.endpoint],
                ["model", settings.rerank.model],
                ["top_k", String(settings.rerank.top_k)],
              ]} />
              <SettingsSection title="Milvus" items={[
                ["uri", settings.milvus.uri],
                ["collection", settings.milvus.collection],
                ["dimension", String(settings.milvus.dimension)],
              ]} />
              <SettingsSection title="对象存储" items={[
                ["endpoint", settings.object_storage.endpoint],
                ["bucket", settings.object_storage.bucket],
                ["region", settings.object_storage.region],
              ]} />
              <SettingsSection title="会话" items={[
                ["history_ttl", `${settings.chat.history_ttl}s`],
              ]} />
              <SettingsSection title="JWT" items={[
                ["algorithm", settings.jwt.algorithm],
                ["expire_minutes", `${settings.jwt.expire_minutes}min`],
              ]} />
            </div>
          ) : (
            <p className="muted">加载中...</p>
          )}
        </section>
      )}
    </div>
  );
}

function SettingsSection({ title, items }: { title: string; items: [string, string][] }) {
  return (
    <div>
      <h4 style={{ margin: "0 0 6px", color: "#3b82f6", fontSize: "0.85rem" }}>{title}</h4>
      {items.map(([k, v]) => (
        <div key={k} style={{ display: "flex", gap: 8, padding: "3px 0" }}>
          <span style={{ color: "#64748b", minWidth: 110, fontSize: "0.82rem" }}>{k}</span>
          <span style={{ wordBreak: "break-all", color: "#1f2933" }}>{v}</span>
        </div>
      ))}
    </div>
  );
}
