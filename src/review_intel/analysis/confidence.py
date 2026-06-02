"""
Confidence scoring engine.

Computes confidence scores for generated insights based on
review volume, source agreement, sentiment consistency,
source quality, and evidence strength.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from review_intel.schemas.analysis import ReviewEvidence
from review_intel.schemas.review import Platform

logger = logging.getLogger(__name__)

# Higher = more trustworthy
PLATFORM_TRUST_SCORES: dict[Platform, float] = {
    Platform.G2: 0.9,
    Platform.CAPTERRA: 0.85,
    Platform.GARTNER: 0.95,
    Platform.TRUSTPILOT: 0.7,
    Platform.PRODUCT_HUNT: 0.6,
    Platform.GOOGLE: 0.5,
    Platform.COMMUNITY: 0.4,
    Platform.UNKNOWN: 0.3,
}


@dataclass
class ConfidenceFactors:
    """Breakdown of confidence score factors."""
    volume_score: float = 0
    agreement_score: float = 0
    consistency_score: float = 0
    quality_score: float = 0
    evidence_score: float = 0
    total: float = 0


def compute_confidence(
    review_count: int,
    evidence: list[ReviewEvidence] | None = None,
    sentiment_values: list[float] | None = None,
    verified_count: int = 0,
    total_count: int = 0,
) -> tuple[float, ConfidenceFactors]:
    """
    Compute confidence score 0-100 with factor breakdown.

    Weights:
      - Review volume: 25%
      - Source agreement (multi-platform): 25%
      - Sentiment consistency: 20%
      - Source quality (verified, trust): 15%
      - Evidence strength (direct quotes): 15%
    """
    factors = ConfidenceFactors()
    evidence = evidence or []
    sentiment_values = sentiment_values or []

    # Volume (0-25): more reviews → higher confidence
    factors.volume_score = min(review_count / 10, 1.0) * 25

    # Source agreement (0-25): reviews from multiple platforms
    unique_sources = len(set(e.source for e in evidence)) if evidence else 1
    factors.agreement_score = min(unique_sources / 3, 1.0) * 25

    # Sentiment consistency (0-20): low variance in sentiment
    if len(sentiment_values) >= 2:
        mean = sum(sentiment_values) / len(sentiment_values)
        variance = sum((v - mean) ** 2 for v in sentiment_values) / len(sentiment_values)
        factors.consistency_score = max(0, (1 - variance)) * 20
    elif len(sentiment_values) == 1:
        factors.consistency_score = 10  # Single data point = medium
    else:
        factors.consistency_score = 0

    # Source quality (0-15): verified reviews and trusted platforms
    if total_count > 0:
        verified_ratio = verified_count / total_count
    else:
        verified_ratio = 0
    platform_trust = 0.5
    if evidence:
        platform_trust = sum(
            PLATFORM_TRUST_SCORES.get(e.source, 0.3) for e in evidence
        ) / len(evidence)
    factors.quality_score = (verified_ratio * 0.5 + platform_trust * 0.5) * 15

    # Evidence strength (0-15): more evidence with direct quotes
    evidence_count = len(evidence)
    avg_quote_len = (
        sum(len(e.quote) for e in evidence) / evidence_count
        if evidence_count > 0 else 0
    )
    quote_quality = min(avg_quote_len / 100, 1.0)  # 100+ char quotes = max
    factors.evidence_score = min(evidence_count / 5, 1.0) * quote_quality * 15

    factors.total = round(
        factors.volume_score + factors.agreement_score +
        factors.consistency_score + factors.quality_score +
        factors.evidence_score,
        1,
    )
    factors.total = min(factors.total, 100)

    return factors.total, factors
