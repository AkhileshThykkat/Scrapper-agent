"""
Step 3: Pain point extraction — categorized, severity-scored complaints.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.domain.ecosystem_context import build_waba_system_context, build_competitor_context
from review_intel.schemas.analysis import SentimentCategory

logger = logging.getLogger(__name__)


class PainPointExtractionStep(AnalysisStep):
    """Extract and categorize pain points with severity scoring."""

    @property
    def name(self) -> str:
        return "pain_point_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        system = build_waba_system_context() + "\n\n" + build_competitor_context(context.company)

        complaints = []
        for ext in context.raw_extractions:
            for c in ext.get("complaints", []):
                complaints.append(c)

        categories = [c.value for c in SentimentCategory]

        # Sample reviews for evidence
        sample_reviews = []
        for r in context.reviews[:50]:
            sample_reviews.append({
                "id": r.id,
                "text": r.text[:200],
                "platform": r.platform.value,
            })

        prompt = f"""From these complaints about "{context.company}", identify the TOP pain points.

Complaints gathered: {json.dumps(complaints[:150])}

Sample reviews for evidence: {json.dumps(sample_reviews[:20])}

Categories to use: {json.dumps(categories)}

For each pain point:
- description: clear description of the pain point
- category: one of the categories above
- frequency: how many reviews mention this
- severity: 0-100 (impact on user experience)
- business_impact: one sentence on business impact
- confidence_score: 0-100

Respond with JSON array:
[{{"description": "...", "category": "...", "frequency": N, "severity": N, "business_impact": "...", "confidence_score": N, "supporting_reviews": []}}]

Rank by severity * frequency. Max 15 pain points."""

        raw = await self.llm.complete(prompt, system, max_tokens=3000)
        if raw:
            try:
                text = raw.strip()
                if text.startswith("```"):
                    text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                data = json.loads(text)
                if isinstance(data, list):
                    context.pain_points = data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Pain point extraction parse failed: %s", e)

        logger.info("Extracted %d pain points", len(context.pain_points))
        return context
