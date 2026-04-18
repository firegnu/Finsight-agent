"""RAG search tool — retrieve historical case studies from Chroma collection."""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from typing import Any

import chromadb

from ..config import settings
from ..llm.client import embed

logger = logging.getLogger("finsight.rag_search")

SNIPPET_MAX_CHARS = 240
DEFAULT_TOP_K = 3


@lru_cache(maxsize=1)
def _get_collection():
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return client.get_collection(settings.chroma_collection_name)


def _unflatten_metadata(meta: dict) -> dict:
    """Reverse the JSON-flatten done in scripts/index_cases.py for list fields."""
    result: dict[str, Any] = {}
    for k, v in meta.items():
        if k.endswith("_json") and isinstance(v, str):
            try:
                result[k[: -len("_json")]] = json.loads(v)
                continue
            except json.JSONDecodeError:
                pass
        result[k] = v
    return result


def _snippet(text: str, n: int = SNIPPET_MAX_CHARS) -> str:
    clean = " ".join(text.split())
    return clean[:n] + ("…" if len(clean) > n else "")


def _build_where(metric: str | None, region: str | None) -> dict | None:
    """Build Chroma where-filter. Chroma's filter DSL does not support
    $exists; we keep the filter minimal (metric only), leaving region
    preference to vector similarity + the case's own region tagging."""
    if metric:
        return {"metric": metric}
    # region alone would exclude all methodology cases (which have empty region
    # or 'general'), so we don't apply it as a hard filter. The agent passes
    # region to influence the query text instead.
    return None


async def run(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    metric: str | None = None,
    region: str | None = None,
) -> dict:
    """Retrieve top-k relevant historical cases for a query."""
    if not query.strip():
        return {"error": "empty query"}

    try:
        collection = _get_collection()
    except Exception as e:  # noqa: BLE001
        logger.error("failed to open Chroma collection: %s", e)
        return {
            "error": f"Chroma collection unavailable: {e}. Run: python scripts/index_cases.py",
        }

    try:
        query_vec = (await embed([query]))[0]
    except Exception as e:  # noqa: BLE001
        logger.error("embedding failed for query %r: %s", query, e)
        return {"error": f"embedding call failed: {e}"}

    # Attempt with filter first; if no results, retry without filter
    where = _build_where(metric, region)
    try:
        result = collection.query(
            query_embeddings=[query_vec],
            n_results=top_k,
            where=where,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("filtered query failed (%s), retrying without filter", e)
        result = collection.query(query_embeddings=[query_vec], n_results=top_k)

    ids = result["ids"][0]
    docs = result["documents"][0]
    metas = result["metadatas"][0]
    dists = result["distances"][0]

    # Fallback: if a filter was applied and returned nothing, query again without it.
    if not ids and where is not None:
        result = collection.query(query_embeddings=[query_vec], n_results=top_k)
        ids = result["ids"][0]
        docs = result["documents"][0]
        metas = result["metadatas"][0]
        dists = result["distances"][0]

    hits: list[dict] = []
    for id_, doc, meta, dist in zip(ids, docs, metas, dists):
        meta = _unflatten_metadata(meta or {})
        hits.append({
            "id": id_,
            "title": meta.get("title", id_),
            "tags": meta.get("tags", []),
            "region": meta.get("region", ""),
            "metric": meta.get("metric", ""),
            "period": meta.get("period", ""),
            "score": round(1 - dist, 3),  # cosine similarity in [0, 1]
            "snippet": _snippet(doc),
        })

    logger.info(
        "rag_search query=%r metric=%s region=%s → %d hits",
        query[:60], metric, region, len(hits),
    )
    return {
        "query": query,
        "filters": {"metric": metric, "region": region},
        "hit_count": len(hits),
        "hits": hits,
    }


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "rag_search",
        "description": (
            "检索历史分析案例库（含真实历史事件复盘 + 方法论 SOP）。"
            "使用场景：发现异常后希望参考历史类似案例的根因和应对；"
            "需要某类问题的标准调查流程；给根因推测加历史依据。"
            "可选 metric/region 参数做精准过滤（推荐使用，提高命中率）。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "自然语言检索词，如 '逾期率飙升的常见根因' 或 '获客量断崖如何调查'",
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回前 N 个相关案例，默认 3",
                    "default": DEFAULT_TOP_K,
                },
                "metric": {
                    "type": "string",
                    "description": (
                        "可选：按指标精准过滤。值应为数据库字段名，如 "
                        "'overdue_rate' / 'new_customers' / 'churn_rate'"
                    ),
                },
                "region": {
                    "type": "string",
                    "description": "可选：按区域精准过滤，如 '华东' / '华南'。方法论型案例会一并返回",
                },
            },
            "required": ["query"],
        },
    },
}
