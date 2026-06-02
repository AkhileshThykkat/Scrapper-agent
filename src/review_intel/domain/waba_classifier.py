"""
WABA review classifier — automatic theme and concept tagging.

Uses rule-based keyword matching as a fast first pass.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from review_intel.domain.waba_taxonomy import CONCEPT_KEYWORDS, THEME_KEYWORDS
from review_intel.schemas.review import ReviewSchema
from review_intel.schemas.waba import WABATheme, WhatsAppConcept

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    review_id: str
    themes: list[WABATheme] = field(default_factory=list)
    concepts: list[WhatsAppConcept] = field(default_factory=list)
    theme_scores: dict[WABATheme, float] = field(default_factory=dict)
    concept_scores: dict[WhatsAppConcept, float] = field(default_factory=dict)

    @property
    def primary_theme(self) -> WABATheme | None:
        if not self.theme_scores:
            return None
        return max(self.theme_scores, key=self.theme_scores.get)  # type: ignore[arg-type]

    @property
    def is_waba_relevant(self) -> bool:
        return len(self.themes) > 0 or len(self.concepts) > 0


class WABAClassifier:
    """Classify reviews against WABA themes and WhatsApp concepts."""

    def __init__(self, theme_threshold: float = 1.0, concept_threshold: float = 1.0):
        self.theme_threshold = theme_threshold
        self.concept_threshold = concept_threshold
        self._theme_patterns: dict[WABATheme, list[re.Pattern]] = {
            theme: [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in kws]
            for theme, kws in THEME_KEYWORDS.items()
        }
        self._concept_patterns: dict[WhatsAppConcept, list[re.Pattern]] = {
            concept: [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in kws]
            for concept, kws in CONCEPT_KEYWORDS.items()
        }

    def classify(self, review: ReviewSchema) -> ClassificationResult:
        text = review.full_text
        result = ClassificationResult(review_id=review.id)
        for theme, patterns in self._theme_patterns.items():
            score = sum(1.0 for p in patterns if p.search(text))
            if score >= self.theme_threshold:
                result.themes.append(theme)
                result.theme_scores[theme] = score
        for concept, patterns in self._concept_patterns.items():
            score = sum(1.0 for p in patterns if p.search(text))
            if score >= self.concept_threshold:
                result.concepts.append(concept)
                result.concept_scores[concept] = score
        return result

    def classify_batch(self, reviews: list[ReviewSchema]) -> list[ClassificationResult]:
        results = [self.classify(r) for r in reviews]
        waba_count = sum(1 for r in results if r.is_waba_relevant)
        logger.info("Classified %d reviews: %d WABA-relevant", len(reviews), waba_count)
        return results

    def get_theme_distribution(self, results: list[ClassificationResult]) -> dict[WABATheme, int]:
        dist: dict[WABATheme, int] = {}
        for r in results:
            for theme in r.themes:
                dist[theme] = dist.get(theme, 0) + 1
        return dict(sorted(dist.items(), key=lambda x: x[1], reverse=True))
