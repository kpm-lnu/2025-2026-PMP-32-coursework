from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class LLMResponse:
    content: str
    tool_call: Optional[Dict[str, Any]] = None
    raw: Optional[Any] = None
