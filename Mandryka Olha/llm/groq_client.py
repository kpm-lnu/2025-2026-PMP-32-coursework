import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests
import json
import re
import time

from .base import BaseLLMClient
from .response import LLMResponse
from .config import CHAT_MODEL

load_dotenv()

class GroqClient(BaseLLMClient):
    HARD_TPM_LIMIT = 6000
    DEFAULT_MAX_OUTPUT_TOKENS = 700
    RETRY_MAX_OUTPUT_TOKENS = 320
    MAX_MESSAGE_CHARS = 4000
    MAX_TOTAL_INPUT_CHARS = 12000
    RETRY_MAX_TOTAL_INPUT_CHARS = 7000
    MAX_429_RETRIES = 2

    def __init__(
        self,
        model_name: str = CHAT_MODEL,
        api_key: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1"
    ):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY")
        self.base_url = base_url
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY або GROK_API_KEY is not set")

    def _estimate_tokens_from_text(self, text: str) -> int:
        return max(1, len(text) // 4)

    def _estimate_messages_tokens(self, messages: List[Dict]) -> int:
        total = 0
        for msg in messages:
            total += self._estimate_tokens_from_text(str(msg.get("content", ""))) + 4
        return total

    def _sanitize_messages(self, messages: List[Dict], max_total_chars: int) -> List[Dict]:
        clean_messages: List[Dict] = []

        for msg in messages:
            role = msg.get("role")
            content = str(msg.get("content", ""))

            if role == "tool":
                role = "user"
                content = f"Tool result: {content}"
            elif role not in {"system", "user", "assistant"}:
                role = "user"

            if len(content) > self.MAX_MESSAGE_CHARS:
                content = content[: self.MAX_MESSAGE_CHARS] + "... [truncated]"

            clean_messages.append({"role": role, "content": content})

        system_msgs = [m for m in clean_messages if m["role"] == "system"]
        non_system = [m for m in clean_messages if m["role"] != "system"]

        selected: List[Dict] = []
        used_chars = 0

        for m in system_msgs:
            if used_chars + len(m["content"]) <= max_total_chars:
                selected.append(m)
                used_chars += len(m["content"])

        remaining = max_total_chars - used_chars
        recent_selected: List[Dict] = []
        for m in reversed(non_system):
            c_len = len(m["content"])
            if c_len <= remaining:
                recent_selected.append(m)
                remaining -= c_len

        selected.extend(reversed(recent_selected))

        if not selected and non_system:
            fallback = non_system[-1].copy()
            fallback["content"] = fallback["content"][: max(500, max_total_chars)]
            selected = [fallback]

        return selected

    def _build_payload(
        self,
        messages: List[Dict],
        json_mode: bool,
        stop: Optional[List[str]],
        max_total_input_chars: int,
        target_max_output_tokens: int,
    ) -> Dict:
        clean_messages = self._sanitize_messages(messages, max_total_chars=max_total_input_chars)
        estimated_input_tokens = self._estimate_messages_tokens(clean_messages)

        safe_max_output = max(
            128,
            min(target_max_output_tokens, self.HARD_TPM_LIMIT - estimated_input_tokens - 200)
        )

        payload = {
            "model": self.model_name,
            "messages": clean_messages,
            "temperature": 0.2,
            "max_tokens": safe_max_output,
            "stream": False
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        if stop:
            payload["stop"] = stop

        return payload

    def _extract_retry_after_seconds(self, error_text: str) -> float:
        if not error_text:
            return 8.0
        match = re.search(r"try again in\s*([0-9]+(?:\.[0-9]+)?)s", error_text, re.IGNORECASE)
        if not match:
            return 8.0
        try:
            return max(1.0, float(match.group(1)))
        except Exception:
            return 8.0

    async def generate(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        stop: Optional[List[str]] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = self._build_payload(
            messages=messages,
            json_mode=json_mode,
            stop=stop,
            max_total_input_chars=self.MAX_TOTAL_INPUT_CHARS,
            target_max_output_tokens=self.DEFAULT_MAX_OUTPUT_TOKENS,
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 413:
                retry_payload = self._build_payload(
                    messages=messages,
                    json_mode=json_mode,
                    stop=stop,
                    max_total_input_chars=self.RETRY_MAX_TOTAL_INPUT_CHARS,
                    target_max_output_tokens=self.RETRY_MAX_OUTPUT_TOKENS,
                )
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=retry_payload,
                    timeout=30
                )

            if response.status_code == 429:
                for retry_idx in range(self.MAX_429_RETRIES):
                    retry_after = self._extract_retry_after_seconds(response.text)
                    wait_seconds = retry_after + 0.5 * (retry_idx + 1)
                    print(f"Groq 429 rate limit. Waiting {wait_seconds:.2f}s before retry...")
                    time.sleep(wait_seconds)

                    retry_payload = self._build_payload(
                        messages=messages,
                        json_mode=json_mode,
                        stop=stop,
                        max_total_input_chars=self.RETRY_MAX_TOTAL_INPUT_CHARS,
                        target_max_output_tokens=self.RETRY_MAX_OUTPUT_TOKENS,
                    )
                    response = requests.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=retry_payload,
                        timeout=30
                    )
                    if response.status_code != 429:
                        break
            
            if response.status_code != 200:
                error_details = response.text
                print(f"Groq API помилка {response.status_code}: {error_details}")
                raise Exception(f"Groq API {response.status_code}: {error_details}")
            
            data = response.json()
            
            if "choices" not in data or not data["choices"]:
                return LLMResponse(
                    content="Groq API повернув порожню відповідь (немає choices)",
                    raw=data
                )
            
            content = data["choices"][0]["message"]["content"]
            
            if not content or content.strip() == "":
                return LLMResponse(
                    content="Groq API повернув порожній контент",
                    raw=data
                )
            
            return LLMResponse(
                content=content,
                raw=data
            )
            
        except requests.exceptions.RequestException as e:
            return LLMResponse(
                content=f"Помилка з'єднання з Groq API: {str(e)}",
                raw=None
            )
        except Exception as e:
            return LLMResponse(
                content=f"Помилка Groq API: {str(e)}",
                raw=None
            )