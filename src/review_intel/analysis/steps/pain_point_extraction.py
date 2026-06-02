"""
Step 3: Pain point extraction — deep-dive with root cause analysis and evidence.
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
    """Extract pain points with root cause analysis, evidence, and business impact."""

    @property
    def name(self) -> str:
        return "pain_point_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        system = build_waba_system_context() + "\n\n" + build_competitor_context(context.company)

        # Gather all complaints with their quotes and severity
        complaints_with_evidence = []
        for ext in context.raw_extractions:
            for c in ext.get("complaints", []):
                if isinstance(c, dict):
                    complaints_with_evidence.append(c)
                else:
                    complaints_with_evidence.append({"what": str(c), "quote": "", "severity": "moderate"})

        # Also gather reviewer context for user segment analysis
        reviewer_contexts = [
            ext.get("reviewer_context", "") for ext in context.raw_extractions
            if ext.get("reviewer_context")
        ]

        categories = [c.value for c in SentimentCategory]

        prompt = f"""You are a senior product analyst preparing a pain point report for "{context.company}" leadership.

You have {len(complaints_with_evidence)} complaints from {len(context.reviews)} reviews.

COMPLAINTS WITH DIRECT EVIDENCE:
{json.dumps(complaints_with_evidence[:120])}

REVIEWER CONTEXTS (who is complaining):
{json.dumps(reviewer_contexts[:50])}

Categories: {json.dumps(categories)}

For each distinct pain point, provide a THOROUGH analysis:

- description: Clear, specific description of the pain point (1-2 sentences)
- category: one of the categories above
- frequency: how many reviews mention this or closely related issues
- severity: 0-100 (consider: how much does this block the user's workflow?)
- confidence_score: 0-100

- root_cause_analysis: 2-4 sentences explaining WHY this problem likely exists. Is it a technical limitation? A design choice? A resource constraint? A platform-level issue (WhatsApp/Meta) vs. a BSP-level issue?

- user_impact: 2-3 sentences on HOW this affects users in practice. What workflow is broken? What workaround do they use? How much time/money does it cost them?

- affected_segments: Which user types are most affected? (e.g., "primarily affects marketing teams doing high-volume broadcasts" or "impacts small businesses with limited technical resources")

- evidence_quotes: 3-5 VERBATIM quotes from the complaints data above that best illustrate this pain point. Use the exact quotes provided — do not paraphrase.

- business_impact: One sentence on the business impact for {context.company} (e.g., churn risk, NPS impact, competitive disadvantage)

- recommended_fix: One concrete, actionable recommendation to address this pain point

Respond with JSON array:
[{{"description": "...", "category": "...", "frequency": N, "severity": N, "confidence_score": N, "root_cause_analysis": "...", "user_impact": "...", "affected_segments": "...", "evidence_quotes": ["...", "..."], "business_impact": "...", "recommended_fix": "...", "supporting_reviews": []}}]

Rank by severity * frequency. Max 12 pain points. Merge similar complaints into single pain points.
Be analytical and specific — avoid generic statements like "users are unhappy"."""

        raw = await self.llm.complete(prompt, system, max_tokens=4096)
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

        logger.info("Extracted %d pain points with root cause analysis", len(context.pain_points))
        return context
