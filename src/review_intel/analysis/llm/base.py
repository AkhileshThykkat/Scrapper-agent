"""
Abstract LLM client — unified interface for all LLM providers.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Protocol for LLM providers with structured output support."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> str:
        """Generate a text completion."""
        ...

    async def complete_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> T | None:
        """Generate a structured response validated against a Pydantic model."""
        import json

        schema = response_model.model_json_schema()
        structured_prompt = (
            f"{prompt}\n\n"
            f"Respond with ONLY valid JSON matching this schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```\n"
            f"No markdown, no explanation, just the JSON object."
        )

        for attempt in range(3):
            raw = await self.complete(
                structured_prompt, system_prompt, max_tokens, temperature,
            )
            if not raw:
                continue

            # Extract JSON from response
            text = raw.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(
                    l for l in lines if not l.strip().startswith("```")
                )

            try:
                data = json.loads(text)
                return response_model.model_validate(data)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(
                    "Structured output parse failed (attempt %d): %s",
                    attempt + 1, e,
                )
                if attempt < 2:
                    structured_prompt = (
                        f"Your previous response was not valid JSON. "
                        f"Error: {e}\n\n{structured_prompt}"
                    )

        logger.error("Failed to get structured output after 3 attempts")
        return None
