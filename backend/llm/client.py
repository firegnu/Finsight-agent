"""Provider-agnostic LLM client with runtime multi-provider switching.

Providers are pre-declared in `.env` (e.g. LMSTUDIO_* + ZHIPU_*) and listed in
`backend.config.PROVIDER_IDS`. Each request picks one by `provider_id`; the
default is `settings.default_provider_id`.

Embedding intentionally stays single-provider — vector spaces are tied to the
model used at index time. Changing the embedding model requires rebuilding the
Chroma collection.

A thin response normalizer merges `reasoning_content` into `content` when the
provider emits separated thinking output (DeepSeek R1, Qwen3 thinking mode,
o1-style models). Providers that don't use reasoning_content are unaffected.
"""
from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ..config import ProviderConfig, settings


class ClientBundle(NamedTuple):
    client: AsyncOpenAI
    model: str
    provider_id: str


@lru_cache(maxsize=32)
def _build_client(base_url: str, api_key: str) -> AsyncOpenAI:
    """Cached AsyncOpenAI factory keyed by (base_url, api_key).

    Cache key uses primitives (not ProviderConfig) so equal credentials always
    reuse the same httpx connection pool.
    """
    return AsyncOpenAI(base_url=base_url, api_key=api_key)


def get_client(provider_id: str | None = None) -> ClientBundle:
    """Resolve provider_id to (AsyncOpenAI, model, provider_id).

    Raises KeyError for unknown or unconfigured providers.
    """
    provider: ProviderConfig = settings.get_provider(provider_id)
    client = _build_client(provider.base_url, provider.api_key)
    return ClientBundle(client=client, model=provider.model, provider_id=provider.id)


def _extract_reasoning(msg) -> str | None:
    rc = getattr(msg, "reasoning_content", None)
    if rc:
        return rc
    extra = getattr(msg, "model_extra", None) or {}
    return extra.get("reasoning_content")


def _normalize(response: ChatCompletion) -> ChatCompletion:
    """Merge reasoning_content into content when content is empty.

    No-op for providers that don't expose reasoning_content.
    """
    for choice in response.choices:
        msg = choice.message
        if not (msg.content or "").strip():
            reasoning = _extract_reasoning(msg)
            if reasoning:
                msg.content = reasoning
    return response


async def chat(provider_id: str | None = None, **kwargs) -> ChatCompletion:
    """Route a chat completion to the selected provider.

    Callers that don't pass `model` get the provider's configured model
    injected automatically. Explicit `model` in kwargs wins.
    """
    bundle = get_client(provider_id)
    kwargs.setdefault("model", bundle.model)
    response = await bundle.client.chat.completions.create(**kwargs)
    return _normalize(response)


# ---- Embedding client (single, fixed provider) ----

_embed_client = AsyncOpenAI(
    base_url=settings.llm_embedding_base_url,
    api_key=settings.llm_embedding_api_key,
)

EMBEDDING_MODEL = settings.llm_embedding_model


async def embed(texts: list[str], model: str | None = None) -> list[list[float]]:
    """Create embeddings using the configured embedding provider."""
    if not texts:
        return []
    response = await _embed_client.embeddings.create(
        model=model or EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
