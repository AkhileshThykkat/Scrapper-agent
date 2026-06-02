"""
Comparison engine — cross-competitor analysis across dimensions.
"""

from __future__ import annotations

import logging

from review_intel.schemas.analysis import ComparisonDimension
from review_intel.schemas.competitor import CompetitorComparison, CompetitorProfile

logger = logging.getLogger(__name__)

COMPARISON_DIMENSIONS = [
    "pricing", "onboarding", "support", "automation",
    "integrations", "reporting", "api_reliability",
    "broadcast_campaigns", "template_management",
    "shared_inbox", "chatbot_builder",
]


class ComparisonEngine:
    """Generate cross-competitor comparison matrices."""

    def compare(self, profiles: dict[str, CompetitorProfile]) -> CompetitorComparison:
        """Compare multiple competitors across standard dimensions."""
        competitor_names = list(profiles.keys())

        dimensions: list[ComparisonDimension] = []
        for dim in COMPARISON_DIMENSIONS:
            scores: dict[str, float] = {}
            for name, profile in profiles.items():
                scores[name] = profile.dimension_scores.get(dim, 50.0)

            dimensions.append(ComparisonDimension(
                dimension=dim,
                scores=scores,
                confidence=self._dimension_confidence(profiles, dim),
            ))

        # Determine best-for recommendations
        best_for: dict[str, str] = {}
        for dim in dimensions:
            if dim.scores:
                best = max(dim.scores, key=dim.scores.get)  # type: ignore
                best_for[dim.dimension] = best

        comparison = CompetitorComparison(
            competitors=competitor_names,
            dimensions=dimensions,
            best_for=best_for,
            summary=self._generate_summary(profiles, dimensions),
        )

        logger.info("Compared %d competitors across %d dimensions", len(competitor_names), len(dimensions))
        return comparison

    @staticmethod
    def _dimension_confidence(profiles: dict[str, CompetitorProfile], dim: str) -> float:
        """Average confidence across competitors for a dimension."""
        scores = [p.dimension_scores.get(dim, 0) for p in profiles.values() if dim in p.dimension_scores]
        if not scores:
            return 30.0
        return min(70.0, 30.0 + len(scores) * 10)

    @staticmethod
    def _generate_summary(profiles: dict[str, CompetitorProfile], dimensions: list[ComparisonDimension]) -> str:
        """Generate a text summary of the comparison."""
        lines = []
        for dim in dimensions:
            if dim.scores:
                best = max(dim.scores, key=dim.scores.get)  # type: ignore
                worst = min(dim.scores, key=dim.scores.get)  # type: ignore
                lines.append(f"- {dim.dimension}: {best} leads ({dim.scores[best]:.0f}), {worst} trails ({dim.scores[worst]:.0f})")
        return "\n".join(lines[:10])
