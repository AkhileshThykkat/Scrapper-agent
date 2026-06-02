"""
Step 1: Raw extraction — extract structured facts from review batches.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.domain.ecosystem_context import build_waba_system_context

logger = logging.getLogger(__name__)


class RawExtractionStep(AnalysisStep):
    """Extract structured facts from review text in batches."""

    def __init__(self, llm: BaseLLMClient, chunk_size: int = 30):
        super().__init__(llm)
        self._chunk_size = chunk_size

    @property
    def name(self) -> str:
        return "raw_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        reviews = context.reviews
        system = build_waba_system_context()

        for i in range(0, len(reviews), self._chunk_size):
            chunk = reviews[i:i + self._chunk_size]
            reviews_text = "\n\n".join(
                f"[R{i + j + 1}] (rating={r.rating}, platform={r.platform.value}) {r.full_text}"
                for j, r in enumerate(chunk)
            )

            prompt = f"""Extract structured facts from these reviews for "{context.company}".

For EACH review, extract:
- sentiment: "positive", "negative", "mixed", or "neutral"
- topics: list of specific topics discussed (use WABA terminology when applicable)
- complaints: list of specific complaints (empty if none)
- praises: list of specific praises (empty if none)
- feature_mentions: list of specific features mentioned
- switching_mentions: any mention of switching from/to another product

Respond with JSON array. Each element:
{{"review_id": "R<N>", "sentiment": "...", "topics": [...], "complaints": [...], "praises": [...], "feature_mentions": [...], "switching_from": null, "switching_to": null}}

Reviews:
{reviews_text}"""

            raw = await self.llm.complete(prompt, system, max_tokens=4096)
            if raw:
                try:
                    text = raw.strip()
                    if text.startswith("```"):
                        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                    data = json.loads(text)
                    if isinstance(data, list):
                        context.raw_extractions.extend(data)
                except (json.JSONDecodeError, Exception) as e:
                    logger.warning("Raw extraction parse failed for batch %d: %s", i, e)

        logger.info("Extracted %d structured records", len(context.raw_extractions))
        return context
