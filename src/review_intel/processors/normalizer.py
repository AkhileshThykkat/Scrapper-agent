"""
Text normalization — clean and standardize review text.
"""

from __future__ import annotations

import logging
import re

from review_intel.processors.pipeline import ProcessingStep
from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)


class NormalizationStep(ProcessingStep):
    """Normalize review text: fix encoding, collapse whitespace, clean artifacts."""

    @property
    def name(self) -> str:
        return "normalization"

    @staticmethod
    def _normalize(text: str) -> str:
        # Smart quotes → ASCII
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        # Dashes
        text = text.replace("\u2013", "-").replace("\u2014", "--")
        # Ellipsis
        text = text.replace("\u2026", "...")
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove zero-width characters
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        return text.strip()

    async def process(self, reviews: list[ReviewSchema]) -> list[ReviewSchema]:
        for review in reviews:
            review.text = self._normalize(review.text)
            if review.title:
                review.title = self._normalize(review.title)
            if review.pros:
                review.pros = self._normalize(review.pros)
            if review.cons:
                review.cons = self._normalize(review.cons)
        logger.info("Normalized %d reviews", len(reviews))
        return reviews
