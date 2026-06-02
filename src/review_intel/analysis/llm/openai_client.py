"""
OpenAI LLM client implementation.
"""

from __future__ import annotations

import logging

from review_intel.analysis.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client with connection reuse."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return f"OpenAI ({self._model})"

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
            logger.error("OpenAI call failed: %s", e)
            return ""
