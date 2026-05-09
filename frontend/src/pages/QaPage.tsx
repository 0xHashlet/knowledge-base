import { useState, useRef, useEffect, useCallback } from "react";
import {
  askQuestion,
  submitFeedbackApi,
  type Citation,
  type QaAskResponse,
} from "../api/client";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  feedback?: "up" | "down";
};

export function QaPage({
  knowledgeBaseIds,
  knowledgeBaseNames,
}: {
  knowledgeBaseIds: string[];
  knowledgeBaseNames: string[];
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || loading || knowledgeBaseIds.length === 0) return;
    setInput("");
    setError(null);
    setLoading(true);

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: question,
      citations: [],
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const resp: QaAskResponse = await askQuestion(
        question,
        knowledgeBaseIds,
        sessionId,
      );
      setSessionId(resp.session_id);
      setMessages((prev) => [
        ...prev,
        {
          id: resp.message.id,
          role: "assistant",
          content: resp.message.content,
          citations: resp.message.citations ?? [],
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "问答请求失败");
    } finally {
      setLoading(false);
    }
  }, [input, loading, knowledgeBaseIds, sessionId]);

  const handleFeedback = async (msgId: string, rating: "up" | "down") => {
    setMessages((prev) =>
      prev.map((m) => (m.id === msgId ? { ...m, feedback: rating } : m)),
    );
    try {
      await submitFeedbackApi(msgId, rating);
    } catch {
      // Feedback failure is silent
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="qa-page">
      <div className="qa-header">
        <h2>知识问答</h2>
        <span className="qa-kb-badge">
          {knowledgeBaseNames.join(", ") || "未选择知识库"}
        </span>
      </div>

      <div className="qa-messages">
        {messages.length === 0 && (
          <div className="qa-empty">
            输入问题，基于已选知识库获取答案
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`qa-message qa-message--${msg.role}`}>
            <div className="qa-message-role">
              {msg.role === "user" ? "你" : "助手"}
            </div>
            <div className="qa-message-content">{msg.content}</div>
            {msg.citations.length > 0 && (
              <div className="qa-citations">
                {msg.citations.map((c, i) => (
                  <div key={i} className="qa-citation-item">
                    <strong>{c.document_title || "源文档"}</strong>
                    <p>{c.chunk_text}</p>
                  </div>
                ))}
              </div>
            )}
            {msg.role === "assistant" && (
              <div className="qa-feedback">
                <button
                  className={`qa-feedback-btn ${msg.feedback === "up" ? "active" : ""}`}
                  onClick={() => handleFeedback(msg.id, "up")}
                  title="有用"
                >👍</button>
                <button
                  className={`qa-feedback-btn ${msg.feedback === "down" ? "active" : ""}`}
                  onClick={() => handleFeedback(msg.id, "down")}
                  title="无用"
                >👎</button>
              </div>
            )}
          </div>
        ))}
        {loading && <div className="qa-loading">思考中...</div>}
        {error && <div className="qa-error">{error}</div>}
        <div ref={endRef} />
      </div>

      <div className="qa-input-area">
        <textarea
          className="qa-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入问题，Enter 发送..."
          rows={2}
          disabled={loading}
        />
        <button className="qa-send-btn" onClick={handleSend} disabled={loading}>
          发送
        </button>
      </div>
    </div>
  );
}
