"""
Competitor intelligence schemas — structured models for cross-competitor analysis.
"""

from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from review_intel.schemas.analysis import (
    ComparisonDimension,
    Insight,
    ReviewEvidence,
)


class CompetitorProfile(BaseModel):
    """Comprehensive profile of a single competitor built from review data."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    platform_category: str = Field(
        default="",
        description="e.g. 'WhatsApp BSP', 'CPaaS', 'CRM'",
    )
    total_reviews: int = Field(ge=0, default=0)
    average_rating: float = Field(ge=0, le=5, default=0)
    rating_trend: str = "stable"  # "improving" | "stable" | "declining"

    # Dimensional scores (0-100)
    dimension_scores: dict[str, float] = Field(
        default_factory=dict,
        description="dimension_name → score (0-100)",
    )

    # Evidence-backed insights
    strengths: list[Insight] = Field(default_factory=list)
    weaknesses: list[Insight] = Field(default_factory=list)
    feature_gaps: list[Insight] = Field(default_factory=list)
    recent_trends: list[Insight] = Field(default_factory=list)

    # Source breakdown
    review_sources: dict[str, int] = Field(
        default_factory=dict,
        description="Platform → review count",
    )


class SwitchingPattern(BaseModel):
    """Detected pattern of users switching between two products."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_product: str
    to_product: str
    frequency: int = Field(ge=1)
    reasons: list[str] = Field(default_factory=list)
    reason_categories: list[str] = Field(
        default_factory=list,
        description="e.g. ['pricing', 'features', 'support']",
    )
    post_switch_satisfaction: Optional[float] = Field(
        default=None, ge=-1.0, le=1.0,
        description="Average sentiment after switching",
    )
    evidence: list[ReviewEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=100, default=50)


class CompetitorComparison(BaseModel):
    """Cross-competitor comparison across multiple dimensions."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    competitors: list[str] = Field(min_length=2)
    dimensions: list[ComparisonDimension] = Field(default_factory=list)
    switching_patterns: list[SwitchingPattern] = Field(default_factory=list)
    summary: str = ""
    best_for: dict[str, str] = Field(
        default_factory=dict,
        description="use_case → recommended_competitor",
    )
    confidence: float = Field(ge=0, le=100, default=50)


class MarketOpportunity(BaseModel):
    """A market opportunity detected from competitor gap analysis."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    demand_score: float = Field(ge=0, le=100, description="How many users want this")
    gap_score: float = Field(ge=0, le=100, description="How poorly served today")
    impact_score: float = Field(ge=0, le=100, description="Potential business impact")
    opportunity_score: float = Field(ge=0, le=100, description="Weighted composite")
    affected_competitors: list[str] = Field(default_factory=list)
    supporting_reviews: list[ReviewEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=100, default=50)
