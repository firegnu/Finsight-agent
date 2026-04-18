"""Load historical case markdowns for the /api/cases endpoint.

Read-only convenience: the vector index is built by scripts/index_cases.py;
this module just surfaces case metadata + content to the UI."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import frontmatter

from ..config import settings


SNIPPET_CHARS = 200


def _snippet(text: str, n: int = SNIPPET_CHARS) -> str:
    stripped = text.lstrip()
    # Skip the first markdown H1 header line if present
    if stripped.startswith("#"):
        stripped = stripped.split("\n", 1)[-1].lstrip()
    compact = " ".join(stripped.split())
    return compact[:n] + ("…" if len(compact) > n else "")


def _parse_case(md_path: Path) -> dict:
    post = frontmatter.load(md_path)
    meta = dict(post.metadata)
    case_id = meta.get("id") or md_path.stem
    tags = meta.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)]
    return {
        "id": case_id,
        "title": meta.get("title", case_id),
        "tags": tags,
        "region": meta.get("region", ""),
        "metric": meta.get("metric", ""),
        "period": meta.get("period", ""),
        "severity": meta.get("severity", ""),
        "source_file": md_path.name,
        "snippet": _snippet(post.content),
        "content": post.content,
    }


@lru_cache(maxsize=1)
def load_all_cases() -> list[dict]:
    cases_dir = Path(settings.rag_cases_dir)
    if not cases_dir.exists():
        return []
    return [_parse_case(p) for p in sorted(cases_dir.glob("*.md"))]


def get_case(case_id: str) -> dict | None:
    for case in load_all_cases():
        if case["id"] == case_id:
            return case
    return None
