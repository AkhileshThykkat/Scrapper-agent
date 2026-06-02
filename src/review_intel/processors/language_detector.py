"""
Language detection and filtering.

Detects review language and filters non-English reviews (or marks for translation).
"""

from __future__ import annotations

import logging

from review_intel.processors.pipeline import ProcessingStep
from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)


class LanguageDetectionStep(ProcessingStep):
    """Detect language and filter non-target-language reviews."""

    def __init__(self, target_languages: set[str] | None = None):
        self._target = target_languages or {"en"}
        self._langdetect_available = False
        try:
            import langdetect  # noqa: F401
            self._langdetect_available = True
        except ImportError:
            logger.warning("langdetect not installed; language detection disabled")

    @property
    def name(self) -> str:
        return "language_detection"

    def _detect(self, text: str) -> str | None:
        if not self._langdetect_available:
            return "en"  # Assume English if detection unavailable
        try:
            from langdetect import detect
            return detect(text)
        except Exception:
            return None

    async def process(self, reviews: list[ReviewSchema]) -> list[ReviewSchema]:
        if not self._langdetect_available:
            for r in reviews:
                r.language = "en"
            return reviews

        result: list[ReviewSchema] = []
        filtered = 0
        for review in reviews:
            lang = self._detect(review.text)
            review.language = lang
            if lang and lang in self._target:
                result.append(review)
            elif lang is None:
                # Keep reviews with undetectable language
                result.append(review)
            else:
                filtered += 1

        logger.info("Language filter: %d non-target-language reviews removed", filtered)
        return result
