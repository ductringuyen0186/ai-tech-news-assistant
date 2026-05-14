"""
Thin async client for Groq's OpenAI-compatible chat completions API.

Used by AgenticResearchService and SummarizationService when
``settings.default_llm_provider == LLMProvider.GROQ``. Two entry points:

* :func:`groq_generate` -- non-streaming, returns the full ``content`` string.
* :func:`groq_stream`   -- async iterator yielding incremental token chunks
                          parsed out of the SSE response.

The Ollama call sites in this codebase pass ``num_predict`` (Ollama's
max-tokens knob) and ``temperature``; we accept the same kwargs so the
dispatch in the caller stays a one-liner.

Groq endpoint:
  POST {base_url}/chat/completions
  Headers: Authorization: Bearer <api_key>, Content-Type: application/json
  Body:    {"model": ..., "messages": [...], "stream": bool,
            "max_tokens": int, "temperature": float}

Streaming format is OpenAI SSE:
  data: {"choices":[{"delta":{"content":"hello"}}]}
  data: {"choices":[{"delta":{"content":" world"}}]}
  data: [DONE]
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, Optional

import httpx

from ..core.config import get_settings
from ..core.exceptions import LLMError

logger = logging.getLogger(__name__)


def _resolve_api_key() -> str:
    settings = get_settings()
    raw = getattr(settings, "groq_api_key", None)
    if raw is None:
        raise LLMError("GROQ_API_KEY is not configured")
    # pydantic SecretStr
    if hasattr(raw, "get_secret_value"):
        key = raw.get_secret_value()
    else:
        key = str(raw)
    if not key:
        raise LLMError("GROQ_API_KEY is empty")
    return key


def _build_messages(prompt: str) -> list[dict]:
    # Groq accepts a single-user message. Our prompts already embed the
    # system instructions inline.
    return [{"role": "user", "content": prompt}]


async def groq_generate(
    prompt: str,
    *,
    model: Optional[str] = None,
    num_predict: int = 512,
    temperature: float = 0.2,
    timeout: Optional[int] = None,
    label: str = "generate",
) -> tuple[str, int]:
    """Non-streaming call. Returns ``(text, token_count)``.

    ``num_predict`` is mapped to OpenAI ``max_tokens``. ``label`` is
    logging-only and matches AgenticResearchService's framing.
    """
    settings = get_settings()
    model = model or settings.groq_model
    timeout = timeout or settings.groq_timeout

    payload = {
        "model": model,
        "messages": _build_messages(prompt),
        "stream": False,
        "max_tokens": int(num_predict),
        "temperature": float(temperature),
        "top_p": 0.9,
    }
    headers = {
        "Authorization": f"Bearer {_resolve_api_key()}",
        "Content-Type": "application/json",
    }
    url = f"{settings.groq_base_url}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except (httpx.HTTPError, OSError) as exc:
        raise LLMError(f"Groq HTTP failure ({label}): {exc}", model=model) from exc

    if resp.status_code != 200:
        raise LLMError(
            f"Groq returned {resp.status_code} ({label}): {resp.text[:300]}",
            model=model,
        )

    data = resp.json()
    try:
        text = (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(
            f"Groq returned malformed response ({label}): {data!r:.300}",
            model=model,
        ) from exc
    if not text:
        raise LLMError(f"Groq returned empty response ({label})", model=model)

    usage = data.get("usage") or {}
    token_count = int(
        usage.get("completion_tokens") or len(text.split())
    )
    return text, token_count


async def groq_stream(
    prompt: str,
    *,
    model: Optional[str] = None,
    num_predict: int = 8192,
    temperature: float = 0.3,
    timeout: Optional[int] = None,
    label: str = "stream",
) -> AsyncGenerator[str, None]:
    """Stream chunks of generated text (OpenAI-style SSE deltas).

    Caps ``max_tokens`` at 1500 to keep ``input_tokens + max_tokens`` under
    Groq's free-tier TPM ceiling (12k for 70B-versatile, 6k for 8b-instant).
    Our synthesis prompt is ~7k tokens; capping output at 1500 gives an
    ~8.5k request which fits the 70b limit with headroom. A 1500-token
    report is roughly 1100 words -- plenty for an executive summary.
    """
    settings = get_settings()
    model = model or settings.groq_model
    timeout = timeout or settings.groq_timeout

    # Free-tier-safe cap. Override the caller's larger num_predict.
    max_tokens = min(int(num_predict), 1500)

    payload = {
        "model": model,
        "messages": _build_messages(prompt),
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": float(temperature),
        "top_p": 0.9,
    }
    headers = {
        "Authorization": f"Bearer {_resolve_api_key()}",
        "Content-Type": "application/json",
    }
    url = f"{settings.groq_base_url}/chat/completions"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    try:
                        err_body = await resp.aread()
                        err_text = err_body.decode("utf-8", "replace")[:300]
                    except Exception:  # noqa: BLE001
                        err_text = ""
                    raise LLMError(
                        f"Groq returned {resp.status_code} ({label}): {err_text}",
                        model=model,
                    )

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue
                    data_str = line[5:].strip()
                    if not data_str or data_str == "[DONE]":
                        if data_str == "[DONE]":
                            break
                        continue
                    try:
                        obj = json.loads(data_str)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    try:
                        choice = obj["choices"][0]
                        delta = choice.get("delta") or {}
                        chunk = delta.get("content")
                    except (KeyError, IndexError, TypeError):
                        chunk = None
                    if chunk:
                        yield chunk
    except (httpx.HTTPError, OSError) as exc:
        raise LLMError(f"Groq HTTP failure ({label}): {exc}", model=model) from exc
