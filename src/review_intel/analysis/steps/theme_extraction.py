"""
Step 2: Theme extraction — identify and score WABA/SaaS themes.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.domain.ecosystem_context import build_waba_system_context
from review_intel.schemas.waba import WABATheme

logger = logging.getLogger(__name__)


class ThemeExtractionStep(AnalysisStep):
    """Identify and score WABA themes from raw extractions."""

    @property
    def name(self) -> str:
        return "theme_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        system = build_waba_system_context()

        # Summarize raw extractions for theme analysis
        topics = []
        for ext in context.raw_extractions:
            topics.extend(ext.get("topics", []))
        complaints = []
        for ext in context.raw_extractions:
            complaints.extend(ext.get("complaints", []))

        themes_list = [t.value for t in WABATheme]

        prompt = f"""Analyze these extracted topics and complaints from reviews of "{context.company}" and identify the major themes.

Available WABA themes: {json.dumps(themes_list)}

Topics mentioned across reviews: {json.dumps(topics[:200])}
Complaints mentioned: {json.dumps(complaints[:100])}

For each relevant theme, provide:
- theme: one of the WABA themes above
- frequency: estimated number of reviews mentioning it
- sentiment_score: -1.0 (very negative) to 1.0 (very positive)
- trend_direction: "improving", "stable", or "declining"
- severity_score: 0-100 (how severe the issues are)
- summary: one-sentence summary of what reviews say about this theme

Respond with JSON array:
[{{"theme": "...", "frequency": N, "sentiment_score": 0.0, "trend_direction": "stable", "severity_score": 50, "summary": "..."}}]

Only include themes with frequency > 0. Order by frequency descending."""

        raw = await self.llm.complete(prompt, system, max_tokens=3000)
        if raw:
            try:
                text = raw.strip()
                if text.startswith("```"):
                    text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                data = json.loads(text)
                if isinstance(data, list):
                    for item in data:
                        item.setdefault("confidence_score", 50)
                        item.setdefault("supporting_reviews", [])
                    context.themes = data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Theme extraction parse failed: %s", e)

        logger.info("Extracted %d themes", len(context.themes))
        return context
