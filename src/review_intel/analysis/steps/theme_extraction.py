"""
Step 2: Theme extraction — deep thematic analysis with evidence and explanation.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.domain.ecosystem_context import build_waba_system_context, build_competitor_context
from review_intel.schemas.waba import WABATheme

logger = logging.getLogger(__name__)


class ThemeExtractionStep(AnalysisStep):
    """Deep thematic analysis with evidence, reasoning, and trend context."""

    @property
    def name(self) -> str:
        return "theme_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        system = build_waba_system_context() + "\n\n" + build_competitor_context(context.company)

        # Gather all extracted data for theme analysis
        all_complaints = []
        all_praises = []
        all_topics = []
        for ext in context.raw_extractions:
            all_topics.extend(ext.get("topics", []))
            for c in ext.get("complaints", []):
                if isinstance(c, dict):
                    all_complaints.append(f"{c.get('what', '')} [quote: \"{c.get('quote', '')}\"] (severity: {c.get('severity', '?')})")
                else:
                    all_complaints.append(str(c))
            for p in ext.get("praises", []):
                if isinstance(p, dict):
                    all_praises.append(f"{p.get('what', '')} [quote: \"{p.get('quote', '')}\"]")
                else:
                    all_praises.append(str(p))

        themes_list = [t.value for t in WABATheme]

        prompt = f"""You are writing a thorough thematic analysis of customer reviews for "{context.company}".

You have {len(context.reviews)} reviews. Here is the extracted data:

TOPICS MENTIONED (frequency matters — repeated topics are significant):
{json.dumps(all_topics[:300])}

COMPLAINTS WITH QUOTES:
{json.dumps(all_complaints[:150])}

PRAISES WITH QUOTES:
{json.dumps(all_praises[:150])}

Available WABA themes: {json.dumps(themes_list)}

For each theme that appears in the data, write a THOROUGH analysis. Not just a score — explain WHAT customers are saying, WHY it matters, and provide EVIDENCE.

For each theme, provide:
- theme: one of the WABA themes above
- frequency: number of reviews touching this theme
- sentiment_score: -1.0 to 1.0
- trend_direction: "improving", "stable", or "declining"
- severity_score: 0-100

- analysis: A 3-5 sentence paragraph explaining:
  1. What customers are specifically saying about this theme
  2. The nature and severity of complaints (with representative quotes)
  3. What's working well (with representative quotes)
  4. The business impact for users of this product
  5. How this compares to industry expectations

- key_quotes: List of 2-4 direct quotes from the extracted data that best represent customer sentiment on this theme
- recommendations: 1-2 actionable recommendations based on the findings

Respond with JSON array:
[{{"theme": "...", "frequency": N, "sentiment_score": 0.0, "trend_direction": "stable", "severity_score": 50, "analysis": "Customers consistently report that...", "key_quotes": ["quote1", "quote2"], "recommendations": ["rec1", "rec2"], "confidence_score": N, "supporting_reviews": []}}]

Only include themes with frequency > 0. Order by severity_score * frequency descending.
Be thorough and analytical — this report goes to product leadership."""

        raw = await self.llm.complete(prompt, system, max_tokens=4096)
        if raw:
            try:
                text = raw.strip()
                if text.startswith("```"):
                    text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                data = json.loads(text)
                if isinstance(data, list):
                    context.themes = data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Theme extraction parse failed: %s", e)

        logger.info("Extracted %d themes with analysis", len(context.themes))
        return context
