"""
Analysis result schemas — structured outputs from the multi-step LLM analysis chain.

Every insight, pain point, feature request, and theme analysis carries:
- confidence_score (0-100)
- supporting evidence (list of ReviewEvidence with review_id, quote, source)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from review_intel.schemas.review import Platform


# ─── Enums ───────────────────────────────────────────────────────────────────


class SentimentCategory(str, Enum):
    """Sentiment dimensions for multi-faceted analysis."""
    SATISFACTION = "satisfaction"
    FRUSTRATION = "frustration"
    DELIGHT = "delight"
    TRUST = "trust"
    VALUE_FOR_MONEY = "value_for_money"
    EASE_OF_USE = "ease_of_use"
    ONBOARDING = "onboarding"
    SUPPORT = "support"
    RELIABILITY = "reliability"
    PERFORMANCE = "performance"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"


class InsightType(str, Enum):
    """Types of generated insights."""
    PAIN_POINT = "pain_point"
    FEATURE_REQUEST = "feature_request"
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    OPPORTUNITY = "opportunity"
    TREND = "trend"


# ─── Evidence ────────────────────────────────────────────────────────────────


class ReviewEvidence(BaseModel):
    """
    A link from an insight back to a specific source review.

    Every generated insight MUST carry at least one ReviewEvidence item
    to prevent hallucination and enable auditability.
    """
    review_id: str
    source: Platform
    quote: str = Field(..., min_length=5, description="Direct quote from the review")
    review_url: Optional[str] = None
    review_date: Optional[datetime] = None


# ─── Core Analysis Models ────────────────────────────────────────────────────


class PainPoint(BaseModel):
    """A categorized customer complaint extracted from reviews."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    category: SentimentCategory
    frequency: int = Field(ge=1, description="Number of reviews mentioning this")
    severity: float = Field(ge=0, le=100, description="Severity score 0-100")
    business_impact: str = ""
    supporting_reviews: list[ReviewEvidence] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=100)


class FeatureRequest(BaseModel):
    """A feature request pattern detected across reviews."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    frequency: int = Field(ge=1)
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    urgency: Literal["low", "medium", "high", "critical"] = "medium"
    supporting_evidence: list[ReviewEvidence] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=100)


class ThemeAnalysis(BaseModel):
    """Analysis of a specific WABA/SaaS theme across reviews."""
    theme: str
    frequency: int = Field(ge=0)
    sentiment_score: float = Field(
        ge=-1.0, le=1.0,
        description="Average sentiment: -1 (negative) to 1 (positive)",
    )
    trend_direction: Literal["improving", "stable", "declining"] = "stable"
    severity_score: float = Field(ge=0, le=100, default=50)
    supporting_reviews: list[ReviewEvidence] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=100, default=50)


class ReviewCluster(BaseModel):
    """A group of semantically similar reviews discovered via embedding clustering."""
    cluster_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    summary: str
    sample_reviews: list[ReviewEvidence] = Field(default_factory=list)
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    confidence_score: float = Field(ge=0, le=100)
    review_count: int = Field(ge=0)


class Insight(BaseModel):
    """
    A generated insight — the primary output of the intelligence platform.

    Every insight is typed, scored for confidence, and backed by evidence.
    Insights without evidence are flagged and excluded from executive summaries.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: InsightType
    title: str
    description: str
    confidence_score: float = Field(ge=0, le=100)
    evidence: list[ReviewEvidence] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence_score >= 70 and len(self.evidence) >= 3

    @property
    def is_evidence_backed(self) -> bool:
        return len(self.evidence) > 0


# ─── Composite Result ────────────────────────────────────────────────────────


class AnalysisResult(BaseModel):
    """Complete output of the multi-step analysis chain for a single company."""
    company: str
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    review_count: int = Field(ge=0)
    source_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="Platform → review count mapping",
    )

    # Step outputs
    themes: list[ThemeAnalysis] = Field(default_factory=list)
    pain_points: list[PainPoint] = Field(default_factory=list)
    feature_requests: list[FeatureRequest] = Field(default_factory=list)
    clusters: list[ReviewCluster] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)

    # Summaries
    executive_summary: str = ""
    overall_sentiment: float = Field(
        default=0.0, ge=-1.0, le=1.0,
        description="Aggregate sentiment score",
    )

    # Quality
    analysis_method: str = ""
    pipeline_metadata: dict = Field(default_factory=dict)

    @property
    def high_confidence_insights(self) -> list[Insight]:
        return [i for i in self.insights if i.is_high_confidence]

    @property
    def critical_pain_points(self) -> list[PainPoint]:
        return sorted(
            [p for p in self.pain_points if p.severity >= 70],
            key=lambda p: p.severity,
            reverse=True,
        )


# ─── Competitor Comparison (used by intelligence layer) ──────────────────────


class ComparisonDimension(BaseModel):
    """A single dimension of comparison between competitors."""
    dimension: str
    scores: dict[str, float] = Field(
        default_factory=dict,
        description="competitor_name → score (0-100)",
    )
    evidence: dict[str, list[ReviewEvidence]] = Field(
        default_factory=dict,
        description="competitor_name → supporting evidence",
    )
    confidence: float = Field(ge=0, le=100, default=50)
