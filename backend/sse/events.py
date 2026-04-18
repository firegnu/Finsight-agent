import json
from typing import Any, Literal

from pydantic import BaseModel


EventType = Literal[
    "start",
    "thinking",
    "tool_call",
    "tool_result",
    "tool_error",
    "final_text",
    "report",
    "done",
    "error",
]


class SSEEvent(BaseModel):
    type: EventType
    data: dict[str, Any] = {}

    def serialize(self) -> str:
        payload = json.dumps(self.model_dump(), ensure_ascii=False, default=str)
        return f"data: {payload}\n\n"
