"""
Core review schema — the normalized representation of a review from any platform.

Every collector must produce ReviewSchema instances. All downstream processing,
analysis, and storage operates on this model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Platform(str, Enum):
    """Supported review source platforms."""
    G2 = "g2"
    CAPTERRA = "capterra"
    TRUSTPILOT = "trustpilot"
    PRODUCT_HUNT = "product_hunt"
    GARTNER = "gartner"
    GOOGLE = "google"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class ReviewSchema(BaseModel):
    """
    Normalized review extracted from any platform.

    This is the single source of truth for review data throughout the pipeline.
    Collectors populate as many fields as the source platform provides.
    """

    # ── Identity ──
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform_review_id: Optional[str] = None

    # ── Content ──
    text: str = Field(..., min_length=10, description="Review body text")
    title: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None

    # ── Rating ──
    rating: Optional[float] = Field(
        default=None, ge=0.0, le=5.0,
        description="Normalized rating on 0-5 scale",
    )

    # ── Temporal ──
    date: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)

    # ── Reviewer ──
    reviewer_name: Optional[str] = None
    reviewer_role: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    verified: bool = False

    # ── Engagement ──
    helpful_votes: int = Field(default=0, ge=0)

    # ── Source ──
    platform: Platform = Platform.UNKNOWN
    review_url: Optional[str] = None
    competitor_name: str = Field(..., min_length=1, description="Product being reviewed")
    product_category: Optional[str] = None

    # ── Raw preservation ──
    raw_html: Optional[str] = Field(
        default=None,
        exclude=True,
        description="Original HTML for reprocessing (excluded from serialization by default)",
    )

    # ── Processing metadata ──
    quality_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Quality score assigned during processing (0-1)",
    )
    language: Optional[str] = Field(
        default=None, max_length=10,
        description="ISO 639-1 language code",
    )
    is_duplicate: bool = False
    is_spam: bool = False

    @field_validator("text")
    @classmethod
    def clean_text(cls, v: str) -> str:
        """Strip and normalize whitespace in review text."""
        return " ".join(v.split())

    @field_validator("competitor_name")
    @classmethod
    def clean_competitor_name(cls, v: str) -> str:
        return v.strip()

    @property
    def has_structured_data(self) -> bool:
        """Whether this review has more than just text."""
        return any([
            self.rating is not None,
            self.date is not None,
            self.reviewer_name is not None,
            self.pros is not None,
            self.cons is not None,
        ])

    @property
    def full_text(self) -> str:
        """Combine title, pros, cons, and body into a single text for analysis."""
        parts = []
        if self.title:
            parts.append(f"Title: {self.title}")
        if self.pros:
            parts.append(f"Pros: {self.pros}")
        if self.cons:
            parts.append(f"Cons: {self.cons}")
        parts.append(self.text)
        return "\n".join(parts)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ReviewSchema):
            return self.id == other.id
        return NotImplemented
