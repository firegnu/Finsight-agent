"""Build the Chroma RAG collection from markdown cases.

Idempotent: drops + recreates the collection on every run. Run:
    python scripts/index_cases.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

import chromadb
import frontmatter

# Allow running from repo root: `python scripts/index_cases.py`
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import settings  # noqa: E402
from backend.llm.client import embed  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("index_cases")


def _flatten_metadata(meta: dict) -> dict:
    """Chroma metadata only accepts str/int/float/bool. Serialize list values
    as JSON strings (with `_json` suffix) so they round-trip."""
    flat: dict[str, str | int | float | bool] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            flat[k] = v
        elif isinstance(v, list):
            flat[f"{k}_json"] = json.dumps(v, ensure_ascii=False)
        elif v is None:
            continue
        else:
            flat[k] = str(v)
    return flat


def _load_cases(cases_dir: Path) -> list[dict]:
    cases = []
    for md_path in sorted(cases_dir.glob("*.md")):
        post = frontmatter.load(md_path)
        meta = dict(post.metadata)
        case_id = meta.get("id") or md_path.stem
        cases.append({
            "id": case_id,
            "title": meta.get("title", case_id),
            "text": post.content,
            "metadata": meta,
            "source_file": md_path.name,
        })
    return cases


async def build_index(cases_dir: Path, db_path: Path, collection_name: str) -> int:
    cases = _load_cases(cases_dir)
    if not cases:
        logger.warning("No case files found in %s", cases_dir)
        return 0

    logger.info("Loaded %d case(s) from %s", len(cases), cases_dir)

    # Embed texts — prepend title + keywords repeatedly so the semantic
    # vector leans toward the case's topic rather than being diluted by body prose.
    # Essential for Chinese embedding models (nomic-embed-text v1.5) which
    # otherwise rank all long finance-prose cases similarly close.
    def _build_input(c: dict) -> str:
        meta = c["metadata"]
        kw = meta.get("keywords", "")
        tags = meta.get("tags", [])
        tags_str = "、".join(tags) if isinstance(tags, list) else str(tags)
        header = f"{c['title']}\n\n分类标签：{tags_str}\n关键词：{kw}\n指标：{meta.get('metric', '')}\n区域：{meta.get('region', '通用')}\n\n"
        # Title appears twice (once in header, once prepended) to boost its weight
        return f"{c['title']}\n{header}\n{c['text']}"

    inputs = [_build_input(c) for c in cases]
    logger.info("Calling embedding API for %d docs...", len(inputs))
    vectors = await embed(inputs)
    if len(vectors) != len(cases):
        raise RuntimeError(
            f"Expected {len(cases)} vectors, got {len(vectors)} from embedding API"
        )
    logger.info("Got %d × %dd vectors", len(vectors), len(vectors[0]))

    # Chroma persistent client
    db_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_path))

    # Drop and rebuild collection
    existing = [c.name for c in client.list_collections()]
    if collection_name in existing:
        client.delete_collection(collection_name)
        logger.info("Dropped existing collection '%s'", collection_name)

    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[c["id"] for c in cases],
        embeddings=vectors,
        documents=[c["text"] for c in cases],
        metadatas=[
            _flatten_metadata({
                **c["metadata"],
                "title": c["title"],
                "source_file": c["source_file"],
            })
            for c in cases
        ],
    )

    logger.info(
        "Indexed %d cases into collection '%s' at %s",
        len(cases), collection_name, db_path,
    )
    return len(cases)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases-dir", default=settings.rag_cases_dir)
    parser.add_argument("--db-path", default=settings.chroma_db_path)
    parser.add_argument("--collection", default=settings.chroma_collection_name)
    args = parser.parse_args()

    count = asyncio.run(build_index(
        Path(args.cases_dir),
        Path(args.db_path),
        args.collection,
    ))
    print(f"[index_cases] indexed {count} case(s)")


if __name__ == "__main__":
    main()
