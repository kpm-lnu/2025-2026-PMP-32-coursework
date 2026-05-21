
from collections import deque
from typing import List, Dict, Optional


class ShortTermMemory:
    MAX_ITEM_CHARS = 1500

    def __init__(self, capacity: int = 10):
        self._buffer = deque(maxlen=capacity)

    def _trim(self, text: str) -> str:
        text = str(text or "")
        if len(text) <= self.MAX_ITEM_CHARS:
            return text
        return text[: self.MAX_ITEM_CHARS] + "... [truncated]"

    def add_user(self, text: str):
        self._buffer.append({
            "role": "user",
            "content": self._trim(text)
        })

    def add_assistant(self, text: str):
        self._buffer.append({
            "role": "assistant",
            "content": self._trim(text)
        })

    def add_tool(self, tool_name: str, result: str):
        self._buffer.append({
            "role": "tool",
            "name": tool_name,
            "content": self._trim(result)
        })

    def to_messages(self) -> List[Dict[str, str]]:
        return list(self._buffer)

    def to_messages(self) -> List[Dict]:
        return list(self._buffer)

    def clear(self):
        self._buffer.clear()
