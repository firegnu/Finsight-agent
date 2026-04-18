"""Provider-agnostic LLM client.

Works unchanged against any OpenAI-compatible backend by switching
LLM_BASE_URL + LLM_API_KEY + LLM_MODEL in .env:
  - LM Studio (local): http://127.0.0.1:1234/v1 + qwen3.5-27b
  - DeepSeek:          https://api.deepseek.com/v1 + deepseek-chat
  - Qwen online:       https://dashscope.aliyuncs.com/compatible-mode/v1 + qwen-plus
  - OpenAI:            https://api.openai.com/v1 + gpt-4o

A thin response normalizer merges `reasoning_content` into `content` when the
provider emits separated thinking output (DeepSeek R1, Qwen3 thinking mode,
o1-style models). Providers that don't use reasoning_content are unaffected.
"""
from __future__ import annotations

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..config import settings


_raw_client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
)

MODEL = settings.llm_model


def _extract_reasoning(msg) -> str | None:
    """Read reasoning_content from either direct attribute or pydantic extras."""
    rc = getattr(msg, "reasoning_content", None)
    if rc:
        return rc
    extra = getattr(msg, "model_extra", None) or {}
    return extra.get("reasoning_content")


def _normalize(response: ChatCompletion) -> ChatCompletion:
    """Merge reasoning_content into content when content is empty.

    No-op for providers that don't expose reasoning_content (OpenAI GPT,
    DeepSeek deepseek-chat, Qwen online qwen-plus). For reasoning providers
    (DeepSeek R1, Qwen3 thinking, o1), surfaces the reasoning as user-visible
    content instead of an opaque hidden field.
    """
    for choice in response.choices:
        msg = choice.message
        if not (msg.content or "").strip():
            reasoning = _extract_reasoning(msg)
            if reasoning:
                msg.content = reasoning
    return response


async def chat(**kwargs) -> ChatCompletion:
    """Wrap raw_client.chat.completions.create with response normalization."""
    response = await _raw_client.chat.completions.create(**kwargs)
    return _normalize(response)


# ---- Embedding client (may point to a different provider than chat) ----

_embed_client = AsyncOpenAI(
    base_url=settings.embedding_base_url,
    api_key=settings.embedding_api_key,
)

EMBEDDING_MODEL = settings.llm_embedding_model


async def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Create embeddings for a batch of texts.

    Returns list of float vectors aligned with `texts` order. Uses the embedding
    provider configured in settings (defaults to same as chat provider).
    """
    if not texts:
        return []
    response = await _embed_client.embeddings.create(
        model=model or EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


# Re-export raw client for advanced use (e.g. streaming). Most callers should use `chat`.
llm = _raw_client
