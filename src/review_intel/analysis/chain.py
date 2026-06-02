"""
Analysis chain — orchestrates multi-step LLM analysis.

Each step receives an AnalysisContext, processes it, and returns
an enriched context. Steps are executed sequentially so each step
can build on previous results.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.config import LLMProvider, get_settings
from review_intel.schemas.analysis import AnalysisResult
from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Mutable context passed through the analysis chain."""
    company: str
    reviews: list[ReviewSchema]

    # Accumulated intermediate results
    raw_extractions: list[dict] = field(default_factory=list)
    themes: list[dict] = field(default_factory=list)
    pain_points: list[dict] = field(default_factory=list)
    feature_requests: list[dict] = field(default_factory=list)
    competitive_intel: dict = field(default_factory=dict)
    roadmap_opportunities: list[dict] = field(default_factory=list)
    executive_summary: str = ""
    overall_sentiment: float = 0.0

    # Metadata
    step_timings: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_result(self) -> AnalysisResult:
        """Convert accumulated context into a final AnalysisResult."""
        from review_intel.schemas.analysis import (
            FeatureRequest,
            Insight,
            InsightType,
            PainPoint,
            ThemeAnalysis,
        )

        settings = get_settings()

        result = AnalysisResult(
            company=self.company,
            review_count=len(self.reviews),
            executive_summary=self.executive_summary,
            overall_sentiment=self.overall_sentiment,
            analysis_method=settings.active_llm_description,
            pipeline_metadata={
                "step_timings": self.step_timings,
                "errors": self.errors,
            },
        )

        # Build source breakdown
        for review in self.reviews:
            platform = review.platform.value
            result.source_breakdown[platform] = result.source_breakdown.get(platform, 0) + 1

        # Convert dicts to typed models (steps produce dicts for flexibility)
        for t in self.themes:
            try:
                result.themes.append(ThemeAnalysis.model_validate(t))
            except Exception:
                pass

        for p in self.pain_points:
            try:
                result.pain_points.append(PainPoint.model_validate(p))
            except Exception:
                pass

        for f in self.feature_requests:
            try:
                result.feature_requests.append(FeatureRequest.model_validate(f))
            except Exception:
                pass

        # Convert roadmap opportunities to insights
        for opp in self.roadmap_opportunities:
            try:
                result.insights.append(Insight(
                    insight_type=InsightType.OPPORTUNITY,
                    title=opp.get("title", ""),
                    description=opp.get("description", ""),
                    confidence_score=opp.get("confidence_score", 50),
                    evidence=opp.get("evidence", []),
                ))
            except Exception:
                pass

        return result


class AnalysisStep:
    """Base class for analysis chain steps."""

    def __init__(self, llm: BaseLLMClient):
        self.llm = llm

    @property
    def name(self) -> str:
        return self.__class__.__name__

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        raise NotImplementedError


class AnalysisChain:
    """Multi-step analysis pipeline with chained reasoning."""

    def __init__(self, llm: BaseLLMClient, steps: list[AnalysisStep] | None = None):
        self.llm = llm
        self.steps = steps or []

    def add_step(self, step: AnalysisStep) -> None:
        self.steps.append(step)

    async def analyze(
        self,
        reviews: list[ReviewSchema],
        company: str,
    ) -> AnalysisResult:
        context = AnalysisContext(company=company, reviews=reviews)

        logger.info(
            "Starting analysis chain for %s (%d reviews, %d steps)",
            company, len(reviews), len(self.steps),
        )

        for step in self.steps:
            step_start = time.monotonic()
            try:
                context = await step.execute(context)
                elapsed = (time.monotonic() - step_start) * 1000
                context.step_timings[step.name] = elapsed
                logger.info("Step '%s' completed in %.0fms", step.name, elapsed)
            except Exception as e:
                elapsed = (time.monotonic() - step_start) * 1000
                context.step_timings[step.name] = elapsed
                context.errors.append(f"{step.name}: {str(e)}")
                logger.error("Step '%s' failed after %.0fms: %s", step.name, elapsed, e)

        result = context.to_result()
        logger.info(
            "Analysis complete for %s: %d themes, %d pain points, %d feature requests, %d insights",
            company, len(result.themes), len(result.pain_points),
            len(result.feature_requests), len(result.insights),
        )
        return result
