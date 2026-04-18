"""Load agent-facing skills (methodology SKILL.md files).

Reads backend/skills/*.md with YAML frontmatter (name, description, category,
applicable_metrics). Skills are shown to the Agent via the `use_skill` tool —
the LLM sees name+description in its system prompt and decides when to load
a skill's full content."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import frontmatter


SKILLS_DIR = Path(__file__).parent


def _parse_skill(md_path: Path) -> dict:
    post = frontmatter.load(md_path)
    meta = dict(post.metadata)
    name = meta.get("name") or md_path.stem
    tags = meta.get("applicable_metrics", [])
    if not isinstance(tags, list):
        tags = [str(tags)]
    return {
        "name": name,
        "description": meta.get("description", ""),
        "category": meta.get("category", "methodology"),
        "applicable_metrics": tags,
        "source_file": md_path.name,
        "content": post.content,
    }


@lru_cache(maxsize=1)
def load_all_skills() -> list[dict]:
    """Return all skills, sorted by name. Cached for the process lifetime."""
    if not SKILLS_DIR.exists():
        return []
    skills = []
    for md_path in sorted(SKILLS_DIR.glob("*.md")):
        if md_path.name == "__init__.py":
            continue
        skills.append(_parse_skill(md_path))
    return skills


def get_skill(name: str) -> dict | None:
    for s in load_all_skills():
        if s["name"] == name:
            return s
    return None


def list_skill_names() -> list[str]:
    return [s["name"] for s in load_all_skills()]
