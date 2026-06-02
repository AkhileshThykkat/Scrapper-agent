"""
Step 4: Feature request extraction — with use case context and prioritization rationale.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep

logger = logging.getLogger(__name__)


class FeatureRequestExtractionStep(AnalysisStep):
    """Detect feature requests with use case reasoning and prioritization context."""

    @property
    def name(self) -> str:
        return "feature_request_extraction"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        # Gather reviews with feature request signals
        request_candidates = []
        for ext in context.raw_extractions:
            complaints = ext.get("complaints", [])
            for c in complaints:
                if isinstance(c, dict):
                    what = c.get("what", "").lower()
                    if any(w in what for w in ["missing", "need", "wish", "lack", "doesn't", "can't", "no support", "add"]):
                        request_candidates.append(c)

        # Also get full review text for context
        review_texts = []
        for r in context.reviews:
            text_lower = r.text.lower()
            if any(p in text_lower for p in [
                "wish", "would be", "should have", "need", "missing",
                "please add", "hope they", "looking forward", "if only",
                "it would be great", "feature request", "doesn't have",
                "can't do", "no way to", "not possible", "limitation",
            ]):
                review_texts.append({"id": r.id[:8], "text": r.text[:400], "platform": r.platform.value, "rating": r.rating})

        if not request_candidates and not review_texts:
            logger.info("No feature request candidates found")
            return context

        prompt = f"""You are analyzing feature requests from customer reviews of "{context.company}".

COMPLAINTS THAT INDICATE MISSING FEATURES:
{json.dumps(request_candidates[:50])}

REVIEW EXCERPTS CONTAINING FEATURE REQUEST LANGUAGE:
{json.dumps(review_texts[:30])}

Identify the distinct feature requests. For each, provide a THOROUGH analysis:

- description: Clear description of what feature or capability is being requested (1-2 sentences)
- frequency: how many reviewers are asking for this
- sentiment_score: -1 to 1 (how frustrated are users about this being missing? -1 = very frustrated, 0 = mild wish)
- urgency: "low", "medium", "high", or "critical"

- use_case: 2-3 sentences explaining WHY users want this feature. What are they trying to accomplish? What job-to-be-done does this serve?

- current_workaround: How are users currently working around this missing feature? (1-2 sentences, or "No known workaround" if it's a blocker)

- evidence_quotes: 2-4 VERBATIM quotes from the data above that express this request

- competitive_context: Do competitors offer this feature? If reviewers mention competitors in the context of this feature, note it. (1 sentence)

- prioritization_rationale: Why should (or shouldn't) the product team prioritize this? Consider: frequency of requests, severity of workarounds, competitive pressure, and implementation complexity. (2-3 sentences)

- confidence_score: 0-100

Respond with JSON array:
[{{"description": "...", "frequency": N, "sentiment_score": 0.0, "urgency": "medium", "use_case": "...", "current_workaround": "...", "evidence_quotes": ["..."], "competitive_context": "...", "prioritization_rationale": "...", "confidence_score": N, "supporting_evidence": []}}]

Group similar requests. Max 10. Rank by urgency then frequency."""

        raw = await self.llm.complete(prompt, "", max_tokens=4096)
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

        logger.info("Extracted %d feature requests with context", len(context.feature_requests))
        return context
