"""
Step 6: Executive summary — comprehensive narrative synthesis of all findings.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep

logger = logging.getLogger(__name__)


class ExecutiveSummaryStep(AnalysisStep):
    """Generate a comprehensive executive narrative from all analysis steps."""

    @property
    def name(self) -> str:
        return "executive_summary"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        # Compute overall sentiment
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

        # Gather key evidence quotes from pain points
        top_pain_point_quotes = []
        for pp in context.pain_points[:5]:
            for q in (pp.get("evidence_quotes") or [])[:2]:
                top_pain_point_quotes.append(q)

        # Gather feature request summaries
        feature_summaries = []
        for fr in context.feature_requests[:5]:
            feature_summaries.append({
                "request": fr.get("description", ""),
                "urgency": fr.get("urgency", ""),
                "use_case": fr.get("use_case", "")[:150],
            })

        prompt = f"""You are the head of product intelligence writing a comprehensive executive report on "{context.company}" based on analysis of {len(context.reviews)} customer reviews.

DATA FROM ANALYSIS:
- Overall sentiment score: {context.overall_sentiment} (scale: -1 very negative to +1 very positive)
- Sentiment breakdown: {sum(1 for s in sentiments if s > 0)} positive, {sum(1 for s in sentiments if s < 0)} negative, {sum(1 for s in sentiments if s == 0)} mixed

THEMES ({len(context.themes)} identified):
{json.dumps([{{"theme": t.get("theme"), "sentiment": t.get("sentiment_score"), "analysis": t.get("analysis", "")[:200]}} for t in context.themes[:8]])}

TOP PAIN POINTS ({len(context.pain_points)} total):
{json.dumps([{{"description": p.get("description"), "severity": p.get("severity"), "root_cause": p.get("root_cause_analysis", "")[:150], "impact": p.get("business_impact", "")}} for p in context.pain_points[:5]])}

KEY CUSTOMER QUOTES:
{json.dumps(top_pain_point_quotes[:10])}

FEATURE REQUESTS ({len(context.feature_requests)} total):
{json.dumps(feature_summaries)}

COMPETITIVE POSITION:
{json.dumps(context.competitive_intel.get("market_position_summary", "Not available"))}

Write a comprehensive executive summary with the following sections. Use markdown formatting:

## Customer Sentiment Overview
2-3 paragraphs: What is the overall customer sentiment? What's driving satisfaction and dissatisfaction? Include specific data points and representative customer quotes.

## Critical Issues Requiring Attention
2-3 paragraphs: What are the most severe pain points? Explain each one with context on root cause, user impact, and why it matters to the business. Reference customer quotes.

## Product Opportunities
1-2 paragraphs: What features are customers asking for and why? Which have the strongest business case? Reference competitive context.

## Competitive Positioning
1-2 paragraphs: How does {context.company} stand relative to competitors? Where is it winning? Where is it losing ground? What are the switching patterns?

## Recommended Actions
A prioritized list of 5-7 specific, actionable recommendations. For each, explain WHY it matters (not just what to do). Reference the evidence that supports each recommendation.

CRITICAL RULES:
- Include direct customer quotes throughout using blockquote format (> "quote")
- Every claim must be traceable to review data — no invented statistics or claims
- Be specific — avoid generic statements like "customers want better support"
- Write for a VP of Product audience — analytical, evidence-based, actionable
- Total length: 800-1200 words"""

        summary = await self.llm.complete(prompt, "", max_tokens=4096)
        if summary:
            context.executive_summary = summary.strip()

        logger.info("Executive summary generated (%d chars)", len(context.executive_summary))
        return context
