"""Unit tests for Pydantic schemas."""

import pytest
from datetime import datetime

from review_intel.schemas.review import Platform, ReviewSchema
from review_intel.schemas.analysis import (
    AnalysisResult, FeatureRequest, Insight, InsightType,
    PainPoint, ReviewEvidence, SentimentCategory, ThemeAnalysis,
)
from review_intel.schemas.competitor import CompetitorProfile, SwitchingPattern
from review_intel.schemas.waba import WABATheme


class TestReviewSchema:
    def test_minimal_review(self):
        r = ReviewSchema(text="This is a test review with enough text", competitor_name="Wati")
        assert r.id  # UUID generated
        assert r.platform == Platform.UNKNOWN
        assert r.text == "This is a test review with enough text"

    def test_full_review(self, sample_review: ReviewSchema):
        assert sample_review.rating == 3.5
        assert sample_review.platform == Platform.G2
        assert sample_review.competitor_name == "Interakt"
        assert sample_review.verified is True
        assert sample_review.has_structured_data is True

    def test_text_validation_min_length(self):
        with pytest.raises(Exception):
            ReviewSchema(text="short", competitor_name="Test")

    def test_rating_validation_bounds(self):
        with pytest.raises(Exception):
            ReviewSchema(text="A valid review text here", competitor_name="Test", rating=6.0)

    def test_full_text_combines_fields(self, sample_review: ReviewSchema):
        full = sample_review.full_text
        assert "Title:" in full
        assert sample_review.text in full

    def test_whitespace_normalization(self):
        r = ReviewSchema(
            text="  This   has    extra   whitespace   and   stuff  ",
            competitor_name="Test",
        )
        assert "  " not in r.text

    def test_serialization_excludes_raw_html(self):
        r = ReviewSchema(
            text="A valid review text here for testing",
            competitor_name="Test",
            raw_html="<p>raw</p>",
        )
        data = r.model_dump()
        assert "raw_html" not in data


class TestAnalysisModels:
    def test_review_evidence(self):
        e = ReviewEvidence(
            review_id="abc-123",
            source=Platform.G2,
            quote="Template approvals take way too long",
        )
        assert e.review_id == "abc-123"

    def test_pain_point(self):
        p = PainPoint(
            description="Template approval delays",
            category=SentimentCategory.FRUSTRATION,
            frequency=15,
            severity=80,
            business_impact="Delays campaign launches",
            confidence_score=75,
        )
        assert p.severity == 80
        assert p.confidence_score == 75

    def test_feature_request(self):
        f = FeatureRequest(
            description="WhatsApp Flows support",
            frequency=8,
            sentiment_score=-0.3,
            urgency="high",
            confidence_score=65,
        )
        assert f.urgency == "high"

    def test_insight_confidence(self):
        evidence = [
            ReviewEvidence(review_id=f"r{i}", source=Platform.G2, quote=f"Evidence {i}")
            for i in range(5)
        ]
        i = Insight(
            insight_type=InsightType.PAIN_POINT,
            title="Test",
            description="Test insight",
            confidence_score=80,
            evidence=evidence,
        )
        assert i.is_high_confidence is True
        assert i.is_evidence_backed is True

    def test_insight_low_confidence(self):
        i = Insight(
            insight_type=InsightType.TREND,
            title="Test",
            description="Weak signal",
            confidence_score=30,
        )
        assert i.is_high_confidence is False
        assert i.is_evidence_backed is False

    def test_analysis_result_critical_pain_points(self):
        result = AnalysisResult(
            company="Interakt",
            review_count=100,
            pain_points=[
                PainPoint(
                    description="API outages",
                    category=SentimentCategory.RELIABILITY,
                    frequency=20, severity=90, confidence_score=80,
                ),
                PainPoint(
                    description="Slow UI",
                    category=SentimentCategory.PERFORMANCE,
                    frequency=5, severity=40, confidence_score=60,
                ),
            ],
        )
        critical = result.critical_pain_points
        assert len(critical) == 1
        assert critical[0].description == "API outages"


class TestCompetitorModels:
    def test_competitor_profile(self):
        p = CompetitorProfile(name="Wati", platform_category="BSP", total_reviews=500)
        assert p.name == "Wati"

    def test_switching_pattern(self):
        s = SwitchingPattern(
            from_product="Wati",
            to_product="Interakt",
            frequency=12,
            reasons=["Pricing", "Better Shopify integration"],
        )
        assert s.frequency == 12
        assert len(s.reasons) == 2


class TestWABAEnums:
    def test_all_themes_have_values(self):
        assert len(WABATheme) == 18

    def test_theme_values(self):
        assert WABATheme.BROADCAST_CAMPAIGNS.value == "broadcast_campaigns"
        assert WABATheme.TEMPLATE_APPROVALS.value == "template_approvals"
