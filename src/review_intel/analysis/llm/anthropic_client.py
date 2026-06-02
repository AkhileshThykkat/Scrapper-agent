"""
Anthropic LLM client implementation.
"""

from __future__ import annotations

import logging

from review_intel.analysis.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic API client with connection reuse."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return f"Anthropic ({self._model})"

    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system_prompt or "You are a professional review analyst.",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.content[0].text
        except Exception as e:
            logger.error("Anthropic call failed: %s", e)
            return ""
