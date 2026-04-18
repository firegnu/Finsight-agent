"""use_skill tool — load a methodology skill on-demand by name.

Mirrors Anthropic's Claude Skills pattern: the LLM sees a list of skill
names + descriptions in its system prompt, and invokes `use_skill` when
it wants the full markdown content of a specific methodology."""
from __future__ import annotations

import logging

from ..skills.loader import get_skill, list_skill_names

logger = logging.getLogger("finsight.use_skill")


async def run(skill_name: str) -> dict:
    """Return the full markdown content of the named skill."""
    skill = get_skill(skill_name)
    if not skill:
        available = list_skill_names()
        return {
            "error": f"unknown skill '{skill_name}'. available: {', '.join(available)}",
        }
    logger.info("use_skill loaded: %s (category=%s)", skill["name"], skill["category"])
    return {
        "name": skill["name"],
        "description": skill["description"],
        "category": skill["category"],
        "applicable_metrics": skill["applicable_metrics"],
        "content": skill["content"],
    }


def _build_schema() -> dict:
    names = list_skill_names()
    return {
        "type": "function",
        "function": {
            "name": "use_skill",
            "description": (
                "按名字加载一个方法论 skill（返回完整 markdown 内容）。"
                "使用场景：面对复杂分析任务时，先加载对应方法论作为执行指引，"
                "确保分析按标准流程展开而不是即兴发挥。"
                "每个 skill 的 description 已在 system prompt 里，根据描述选择最匹配的。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "enum": names,
                        "description": "要加载的 skill 名字",
                    },
                },
                "required": ["skill_name"],
            },
        },
    }


TOOL_SCHEMA = _build_schema()
