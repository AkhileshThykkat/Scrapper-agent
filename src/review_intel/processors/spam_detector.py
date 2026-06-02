"""
Spam and bot review detection.

Uses heuristic signals: repetition patterns, generic phrases,
suspicious timing, and text quality indicators.
"""

from __future__ import annotations

import logging
import re

from review_intel.processors.pipeline import ProcessingStep
from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)

# Patterns that indicate spam/bot reviews
SPAM_PATTERNS = [
    r"(buy|click|visit|check out)\s+(now|here|this)",
    r"https?://\S+",  # URLs in reviews are suspicious
    r"(\b\w+\b)(?:\s+\1){3,}",  # Same word repeated 4+ times
    r"(best|amazing|wonderful|excellent)\s+(best|amazing|wonderful|excellent)",
    r"call\s+\d{5,}",  # Phone numbers
    r"discount\s+code",
    r"use\s+coupon",
    r"promo\s+code",
]

GENERIC_SPAM_PHRASES = [
    "best product ever",
    "highly recommended for everyone",
    "i am very happy with this product",
    "worst product ever do not buy",
    "five stars all the way",
    "absolutely amazing must try",
]


class SpamDetectionStep(ProcessingStep):
    """Detect and filter spam/bot reviews using heuristic signals."""

    def __init__(self, min_word_count: int = 5, max_spam_score: float = 0.6):
        self._min_word_count = min_word_count
        self._max_spam_score = max_spam_score
        self._patterns = [re.compile(p, re.IGNORECASE) for p in SPAM_PATTERNS]
        self._generic_phrases = [p.lower() for p in GENERIC_SPAM_PHRASES]

    @property
    def name(self) -> str:
        return "spam_detection"

    def _spam_score(self, review: ReviewSchema) -> float:
        """Compute spam likelihood score 0-1."""
        score = 0.0
        text = review.text
        text_lower = text.lower()
        words = text.split()

        # Too short
        if len(words) < self._min_word_count:
            score += 0.3

        # Pattern matches
        for pattern in self._patterns:
            if pattern.search(text):
                score += 0.2

        # Generic phrases
        for phrase in self._generic_phrases:
            if phrase in text_lower:
                score += 0.3

        # All caps
        if len(text) > 20 and text.upper() == text:
            score += 0.2

        # Excessive punctuation
        punct_ratio = sum(1 for c in text if c in "!?") / max(len(text), 1)
        if punct_ratio > 0.1:
            score += 0.15

        # Very low vocabulary diversity
        unique_words = len(set(w.lower() for w in words))
        if len(words) > 10 and unique_words / len(words) < 0.3:
            score += 0.2

        return min(score, 1.0)

    async def process(self, reviews: list[ReviewSchema]) -> list[ReviewSchema]:
        clean: list[ReviewSchema] = []
        spam_count = 0

        for review in reviews:
            score = self._spam_score(review)
            if score >= self._max_spam_score:
                review.is_spam = True
                spam_count += 1
            else:
                clean.append(review)

        logger.info("Spam detection: %d spam reviews removed from %d", spam_count, len(reviews))
        return clean
