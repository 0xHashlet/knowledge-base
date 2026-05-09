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


from collections.abc import Generator


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
        stream_client=None,
    ) -> None:
        self._client = client
        self._stream_client = stream_client or client
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

        messages = self._build_messages(context, question, history)
        return self._client(messages)

    def generate_stream(
        self,
        *,
        context: str,
        question: str,
        history: list[LlmMessage] | None = None,
    ) -> Generator[str, None, None]:
        if not context.strip():
            yield "未找到相关文档，无法回答您的问题。"
            return

        messages = self._build_messages(context, question, history)
        yield from self._stream_client(messages)

    def _build_messages(
        self, context: str, question: str, history: list[LlmMessage] | None
    ) -> list[LlmMessage]:
        messages = [LlmMessage(role="system", content=self._system_prompt)]
        if history:
            messages.extend(history)
        user_content = f"参考文档：\n{context}\n\n问题：{question}"
        messages.append(LlmMessage(role="user", content=user_content))
        return messages


def create_llm_service(
    endpoint: str,
    model: str,
    system_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    api_key: str = "",
) -> LlmService:
    """Factory for OpenAI-compatible chat completion endpoint using httpx."""
    import json as _json
    import httpx

    api_base = endpoint.rstrip("/")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

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
            headers=headers,
            timeout=120.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _stream(messages: list[LlmMessage]):
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        with httpx.stream(
            "POST",
            f"{api_base}/chat/completions",
            json=body,
            headers=headers,
            timeout=120.0,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except _json.JSONDecodeError:
                        continue

    return LlmService(
        client=_complete,
        stream_client=_stream,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
