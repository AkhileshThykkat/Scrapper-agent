"""
Deduplication — exact and fuzzy duplicate detection.

Uses exact text matching plus SimHash for near-duplicate detection.
"""

from __future__ import annotations

import hashlib
import logging
from collections import defaultdict

from review_intel.processors.pipeline import ProcessingStep
from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)


def _normalize_for_dedup(text: str) -> str:
    """Normalize text for dedup comparison."""
    return " ".join(text.lower().split())


def _simhash(text: str, hashbits: int = 64) -> int:
    """Compute SimHash for near-duplicate detection."""
    tokens = text.lower().split()
    v = [0] * hashbits
    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(hashbits):
            if h & (1 << i):
                v[i] += 1
            else:
                v[i] -= 1
    fingerprint = 0
    for i in range(hashbits):
        if v[i] > 0:
            fingerprint |= 1 << i
    return fingerprint


def _hamming_distance(a: int, b: int) -> int:
    """Count differing bits between two integers."""
    return bin(a ^ b).count("1")


class DeduplicationStep(ProcessingStep):
    """Remove exact and near-duplicate reviews."""

    def __init__(self, similarity_threshold: int = 5):
        self._similarity_threshold = similarity_threshold

    @property
    def name(self) -> str:
        return "deduplication"

    async def process(self, reviews: list[ReviewSchema]) -> list[ReviewSchema]:
        if not reviews:
            return reviews

        # Phase 1: Exact dedup
        seen_exact: dict[str, ReviewSchema] = {}
        after_exact: list[ReviewSchema] = []
        exact_dupes = 0

        for review in reviews:
            norm = _normalize_for_dedup(review.text)
            if norm in seen_exact:
                review.is_duplicate = True
                exact_dupes += 1
            else:
                seen_exact[norm] = review
                after_exact.append(review)

        # Phase 2: Fuzzy dedup via SimHash
        hashes: list[tuple[int, ReviewSchema]] = []
        unique: list[ReviewSchema] = []
        fuzzy_dupes = 0

        for review in after_exact:
            h = _simhash(review.text)
            is_dup = False
            for existing_hash, _ in hashes:
                if _hamming_distance(h, existing_hash) <= self._similarity_threshold:
                    review.is_duplicate = True
                    is_dup = True
                    fuzzy_dupes += 1
                    break
            if not is_dup:
                hashes.append((h, review))
                unique.append(review)

        logger.info(
            "Dedup: %d exact + %d fuzzy duplicates removed from %d reviews",
            exact_dupes, fuzzy_dupes, len(reviews),
        )
        return unique
