"""
Review quality scoring.

Assigns a quality score (0-1) based on: length, specificity,
presence of structured data, and content richness.
"""

from __future__ import annotations

import logging
import re

from review_intel.processors.pipeline import ProcessingStep
from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)

# Words indicating specific, actionable feedback
SPECIFICITY_INDICATORS = [
    "feature", "bug", "crash", "template", "broadcast", "integration",
    "api", "webhook", "chatbot", "automation", "pricing", "onboarding",
    "dashboard", "analytics", "support", "inbox", "campaign", "flow",
    "catalog", "crm", "contact", "message", "notification", "billing",
]


class QualityScoringStep(ProcessingStep):
    """Score review quality and optionally filter low-quality reviews."""

    def __init__(self, min_quality: float = 0.15):
        self._min_quality = min_quality

    @property
    def name(self) -> str:
        return "quality_scoring"

    def _score(self, review: ReviewSchema) -> float:
        """Compute quality score 0-1."""
        score = 0.0
        text = review.full_text
        words = text.split()
        word_count = len(words)

        # Length score (0-0.25)
        if word_count >= 50:
            score += 0.25
        elif word_count >= 20:
            score += 0.15
        elif word_count >= 10:
            score += 0.05

        # Specificity (0-0.25)
        text_lower = text.lower()
        matches = sum(1 for ind in SPECIFICITY_INDICATORS if ind in text_lower)
        score += min(matches / 5, 1.0) * 0.25

        # Structured data bonus (0-0.2)
        if review.rating is not None:
            score += 0.05
        if review.date is not None:
            score += 0.03
        if review.reviewer_name:
            score += 0.02
        if review.pros or review.cons:
            score += 0.05
        if review.verified:
            score += 0.05

        # Sentence structure (0-0.15)
        sentences = re.split(r"[.!?]+", text)
        if len(sentences) >= 3:
            score += 0.15
        elif len(sentences) >= 2:
            score += 0.08

        # Vocabulary diversity (0-0.15)
        unique = len(set(w.lower() for w in words))
        diversity = unique / max(word_count, 1)
        score += diversity * 0.15

        return min(round(score, 3), 1.0)

    async def process(self, reviews: list[ReviewSchema]) -> list[ReviewSchema]:
        result: list[ReviewSchema] = []
        removed = 0

        for review in reviews:
            review.quality_score = self._score(review)
            if review.quality_score >= self._min_quality:
                result.append(review)
            else:
                removed += 1

        logger.info(
            "Quality scoring: %d low-quality reviews removed (threshold=%.2f)",
            removed, self._min_quality,
        )
        return result
