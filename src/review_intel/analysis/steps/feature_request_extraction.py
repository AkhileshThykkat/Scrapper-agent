"""
Step 4: Feature request extraction — detect "I wish" patterns.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep

logger = logging.getLogger(__name__)


class FeatureRequestExtractionStep(AnalysisStep):
    """Detect feature request patterns in reviews."""

    @property
    def name(self) -> str:
        return "feature_request_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        # Gather review texts that may contain feature requests
        request_candidates = []
        for r in context.reviews:
            text_lower = r.text.lower()
            if any(p in text_lower for p in [
                "wish", "would be", "should have", "need", "missing",
                "please add", "hope they", "looking forward", "if only",
                "it would be great", "feature request", "suggestion",
                "want", "require", "lack", "doesn't have", "can't do",
            ]):
                request_candidates.append({
                    "id": r.id, "text": r.text[:300],
                    "platform": r.platform.value,
                })

        if not request_candidates:
            logger.info("No feature request candidates found")
            return context

        prompt = f"""Analyze these review excerpts from "{context.company}" that may contain feature requests.

Reviews: {json.dumps(request_candidates[:40])}

Extract distinct feature requests. For each:
- description: what feature is being requested
- frequency: estimated mentions across all reviews
- sentiment_score: -1 to 1 (urgency/frustration level)
- urgency: "low", "medium", "high", or "critical"
- confidence_score: 0-100

Respond with JSON array:
[{{"description": "...", "frequency": N, "sentiment_score": 0.0, "urgency": "medium", "confidence_score": N, "supporting_evidence": []}}]

Group similar requests. Max 10 feature requests."""

        raw = await self.llm.complete(prompt, "", max_tokens=2500)
        if raw:
            try:
                text = raw.strip()
                if text.startswith("```"):
                    text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                data = json.loads(text)
                if isinstance(data, list):
                    context.feature_requests = data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Feature request parse failed: %s", e)

        logger.info("Extracted %d feature requests", len(context.feature_requests))
        return context
