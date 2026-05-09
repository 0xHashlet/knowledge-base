import { FormEvent, useState } from "react";
import { Database, LockKeyhole } from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";

import { login } from "../api/client";
import { useAuth } from "../state/auth";

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (auth.isAuthenticated) {
    return <Navigate to="/app" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const result = await login(username, password);
      auth.setSession(result.access_token);
      navigate("/app");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <div className="brand-row">
          <div className="brand-icon">
            <Database size={24} />
          </div>
          <div>
            <h1>权限感知企业知识库</h1>
            <p>企业 RAG 管理台</p>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            账号
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="邮箱或用户名"
              autoComplete="username"
            />
          </label>
          <label>
            密码
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="密码"
              type="password"
              autoComplete="current-password"
            />
          </label>
          {error ? <div className="error-banner">{error}</div> : null}
          <button className="primary-button" disabled={submitting} type="submit">
            <LockKeyhole size={18} />
            {submitting ? "登录中" : "登录"}
          </button>
        </form>
      </section>
    </main>
  );
}
