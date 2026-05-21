# llm/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from .response import LLMResponse


class BaseLLMClient(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
    ) -> LLMResponse:
    
        raise NotImplementedError
