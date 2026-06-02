"""
Step 5: Competitive intelligence — extract competitor mentions and comparisons.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.domain.platform_registry import PLATFORMS

logger = logging.getLogger(__name__)


class CompetitiveIntelStep(AnalysisStep):
    """Extract competitive intelligence from reviews."""

    @property
    def name(self) -> str:
        return "competitive_intel"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        # Find reviews mentioning competitors
        competitor_names = [p.name for p in PLATFORMS.values()]
        mentions = []
        for r in context.reviews:
            text_lower = r.text.lower()
            mentioned = [
                name for name in competitor_names
                if name.lower() in text_lower and name.lower() != context.company.lower()
            ]
            if mentioned:
                mentions.append({
                    "review_id": r.id,
                    "text": r.text[:300],
                    "competitors_mentioned": mentioned,
                })

        switching = [
            ext for ext in context.raw_extractions
            if ext.get("switching_from") or ext.get("switching_to")
        ]

        if not mentions and not switching:
            logger.info("No competitor mentions found")
            return context

        prompt = f"""Analyze competitive intelligence from reviews of "{context.company}".

Reviews mentioning competitors: {json.dumps(mentions[:30])}
Switching mentions: {json.dumps(switching[:20])}

Generate:
1. strengths: what customers say {context.company} does better than competitors
2. weaknesses: what customers say competitors do better
3. switching_reasons: why users switch to/from {context.company}
4. market_position: one paragraph summary of competitive position

Respond with JSON:
{{"strengths": ["..."], "weaknesses": ["..."], "switching_reasons": [{{"from": "...", "to": "...", "reason": "..."}}], "market_position": "..."}}"""

        raw = await self.llm.complete(prompt, "", max_tokens=2500)
        if raw:
            try:
                text = raw.strip()
                if text.startswith("```"):
                    text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                context.competitive_intel = json.loads(text)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Competitive intel parse failed: %s", e)

        logger.info("Competitive intel: %d data points", len(context.competitive_intel))
        return context
