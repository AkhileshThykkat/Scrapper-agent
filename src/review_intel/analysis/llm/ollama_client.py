"""
Ollama (local model) LLM client implementation.
"""

from __future__ import annotations

import logging

from review_intel.analysis.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class OllamaClient(BaseLLMClient):
    """Local LLM client via Ollama's OpenAI-compatible API."""

    def __init__(self, base_url: str, model: str = "gemma3:12b"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(
            base_url=base_url.rstrip("/") + "/v1",
            api_key="ollama",
        )
        self._model = model

    @property
    def provider_name(self) -> str:
        return f"Ollama ({self._model})"

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("Ollama call failed: %s", e)
            return ""
