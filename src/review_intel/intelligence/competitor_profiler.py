"""
Competitor profiler — build evidence-backed competitor profiles from reviews.
"""

from __future__ import annotations

import logging

from review_intel.analysis.confidence import compute_confidence
from review_intel.schemas.analysis import (
    AnalysisResult,
    Insight,
    InsightType,
    ReviewEvidence,
)
from review_intel.schemas.competitor import CompetitorProfile

logger = logging.getLogger(__name__)


class CompetitorProfiler:
    """Build structured competitor profiles from analysis results."""

    def build_profile(self, result: AnalysisResult) -> CompetitorProfile:
        """Build a CompetitorProfile from an AnalysisResult."""
        strengths: list[Insight] = []
        weaknesses: list[Insight] = []
        feature_gaps: list[Insight] = []

        # Convert pain points to weakness insights
        for pp in result.pain_points:
            weaknesses.append(Insight(
                insight_type=InsightType.WEAKNESS,
                title=pp.description[:80],
                description=pp.description,
                confidence_score=pp.confidence_score,
                evidence=pp.supporting_reviews,
                metadata={"severity": pp.severity, "category": pp.category.value},
            ))

        # Convert feature requests to feature gap insights
        for fr in result.feature_requests:
            feature_gaps.append(Insight(
                insight_type=InsightType.FEATURE_REQUEST,
                title=fr.description[:80],
                description=fr.description,
                confidence_score=fr.confidence_score,
                evidence=fr.supporting_evidence,
                metadata={"urgency": fr.urgency, "frequency": fr.frequency},
            ))

        # Extract strengths from positive themes
        for theme in result.themes:
            if theme.sentiment_score > 0.3:
                strengths.append(Insight(
                    insight_type=InsightType.STRENGTH,
                    title=f"Strong {theme.theme}",
                    description=f"Customers rate {theme.theme} positively (sentiment: {theme.sentiment_score:.2f})",
                    confidence_score=theme.confidence_score,
                    evidence=theme.supporting_reviews,
                ))

        # Build dimension scores from themes
        dimension_scores: dict[str, float] = {}
        for theme in result.themes:
            score = max(0, min(100, (theme.sentiment_score + 1) * 50))
            dimension_scores[theme.theme] = round(score, 1)

        # Compute average rating
        avg_rating = 0.0
        source_breakdown = result.source_breakdown

        profile = CompetitorProfile(
            name=result.company,
            total_reviews=result.review_count,
            average_rating=avg_rating,
            dimension_scores=dimension_scores,
            strengths=strengths,
            weaknesses=weaknesses,
            feature_gaps=feature_gaps,
            review_sources=source_breakdown,
        )

        logger.info(
            "Built profile for %s: %d strengths, %d weaknesses, %d gaps",
            result.company, len(strengths), len(weaknesses), len(feature_gaps),
        )
        return profile

    def build_profiles(self, results: dict[str, AnalysisResult]) -> dict[str, CompetitorProfile]:
        """Build profiles for multiple competitors."""
        return {name: self.build_profile(result) for name, result in results.items()}
