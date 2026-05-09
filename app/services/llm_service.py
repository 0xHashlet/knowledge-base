from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LlmMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


def chatml_format(messages: list[LlmMessage]) -> str:
    """Format messages using ChatML for strict prompt isolation."""
    parts = []
    for msg in messages:
        parts.append(f"<{msg.role}>\n{msg.content}\n</{msg.role}>")
    return "\n".join(parts)


class LlmService:
    """Calls an OpenAI-compatible chat completion endpoint (vLLM / Ollama)."""

    def __init__(
        self,
        *,
        client,
        system_prompt: str,
        model: str = "default",
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> None:
        self._client = client
        self._system_prompt = system_prompt
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    def generate(
        self,
        *,
        context: str,
        question: str,
        history: list[LlmMessage] | None = None,
    ) -> str:
        if not context.strip():
            return "未找到相关文档，无法回答您的问题。"

        messages = [LlmMessage(role="system", content=self._system_prompt)]
        if history:
            messages.extend(history)
        user_content = f"参考文档：\n{context}\n\n问题：{question}"
        messages.append(LlmMessage(role="user", content=user_content))

        return self._client.complete(messages)


def create_llm_service(
    endpoint: str,
    model: str,
    system_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> LlmService:
    """Factory for OpenAI-compatible chat completion endpoint using httpx."""
    import httpx

    api_base = endpoint.rstrip("/")

    def _complete(messages: list[LlmMessage]) -> str:
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        resp = httpx.post(
            f"{api_base}/chat/completions",
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    return LlmService(
        client=_complete,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
