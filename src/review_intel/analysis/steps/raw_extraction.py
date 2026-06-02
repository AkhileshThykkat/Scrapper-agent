"""
Step 1: Raw extraction — extract structured facts with direct quotes from reviews.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.domain.ecosystem_context import build_waba_system_context

logger = logging.getLogger(__name__)


class RawExtractionStep(AnalysisStep):
    """Extract structured facts with verbatim evidence from review batches."""

    def __init__(self, llm: BaseLLMClient, chunk_size: int = 25):
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
                f"[R{i + j + 1}] (id={r.id[:8]}, rating={r.rating}, platform={r.platform.value})\n{r.full_text}"
                for j, r in enumerate(chunk)
            )

            prompt = f"""You are analyzing customer reviews for "{context.company}".

Read each review carefully and extract DETAILED structured data.

For EACH review, extract:
- review_ref: the review reference (e.g. "R1")
- sentiment: "positive", "negative", "mixed", or "neutral"
- sentiment_explanation: WHY you classified the sentiment this way — reference specific language from the review
- topics: list of specific topics discussed (use WABA-specific terminology: "template approvals", "broadcast campaigns", "shared inbox", etc.)
- complaints: list of specific complaints. For each complaint, include:
  - what: the specific issue
  - quote: the EXACT words from the review that express this complaint (verbatim, 10-50 words)
  - severity: "minor", "moderate", "major", or "critical"
- praises: list of specific praises. For each praise, include:
  - what: the specific positive aspect
  - quote: EXACT words from the review (verbatim)
  - strength: "mild", "moderate", "strong", or "enthusiastic"
- feature_mentions: list of specific product features mentioned with context on whether the mention is positive, negative, or neutral
- switching_from: if the reviewer mentions switching FROM another product, name it and quote the reason
- switching_to: if the reviewer mentions switching TO another product, name it and quote the reason
- reviewer_context: any context about who the reviewer is (role, company size, industry, use case)

CRITICAL RULES:
- Every complaint and praise MUST include a direct quote from the review text
- Do NOT paraphrase — use the reviewer's exact words
- If you cannot find a direct quote, do not invent one
- Distinguish between the BSP's own issues and WhatsApp platform-level issues

Respond with a JSON array. Example element:
{{"review_ref": "R1", "sentiment": "mixed", "sentiment_explanation": "The reviewer praises the broadcast feature but expresses frustration with template approval delays, using words like 'frustrating' and 'waste of time'", "topics": ["broadcast_campaigns", "template_approvals"], "complaints": [{{"what": "Template approvals take 3-4 days", "quote": "template approvals take way too long, sometimes 3-4 business days", "severity": "major"}}], "praises": [{{"what": "Easy broadcast setup", "quote": "setting up broadcast campaigns is incredibly easy and intuitive", "strength": "strong"}}], "feature_mentions": ["broadcast campaigns (positive)", "template management (negative)"], "switching_from": {{"product": "Wati", "reason": "pricing was too expensive for our team size"}}, "switching_to": null, "reviewer_context": "Marketing Manager at an e-commerce company with 51-200 employees"}}

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

        logger.info("Extracted %d structured records with evidence", len(context.raw_extractions))
        return context
