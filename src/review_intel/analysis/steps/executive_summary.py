"""
Step 7: Executive summary — evidence-backed summary of all findings.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep

logger = logging.getLogger(__name__)


class ExecutiveSummaryStep(AnalysisStep):
    """Generate evidence-backed executive summary from all previous steps."""

    @property
    def name(self) -> str:
        return "executive_summary"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        # Compute overall sentiment from raw extractions
        sentiments = []
        for ext in context.raw_extractions:
            s = ext.get("sentiment", "neutral")
            if s == "positive":
                sentiments.append(1.0)
            elif s == "negative":
                sentiments.append(-1.0)
            elif s == "mixed":
                sentiments.append(0.0)
        if sentiments:
            context.overall_sentiment = round(sum(sentiments) / len(sentiments), 2)

        prompt = f"""Generate an executive summary for the review analysis of "{context.company}".

Data from analysis:
- {len(context.reviews)} reviews analyzed
- Overall sentiment: {context.overall_sentiment}
- Themes found: {json.dumps([t.get("theme", "") for t in context.themes[:10]])}
- Top pain points: {json.dumps([p.get("description", "") for p in context.pain_points[:5]])}
- Feature requests: {json.dumps([f.get("description", "") for f in context.feature_requests[:5]])}
- Competitive intel: {json.dumps(context.competitive_intel.get("market_position", ""))}

Write a 3-5 paragraph executive summary that:
1. Opens with the overall customer sentiment and review volume
2. Highlights the top 3 pain points with their severity
3. Summarizes key feature requests
4. Notes competitive positioning if available
5. Closes with recommended priority actions

Be concise and factual. Reference specific findings from the data above.
Do not invent details not present in the data."""

        summary = await self.llm.complete(prompt, "", max_tokens=2000)
        if summary:
            context.executive_summary = summary.strip()

        logger.info("Executive summary generated (%d chars)", len(context.executive_summary))
        return context
