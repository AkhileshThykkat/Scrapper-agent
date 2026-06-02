"""Unit tests for WABA classifier and confidence scoring."""

import pytest

from review_intel.domain.waba_classifier import WABAClassifier
from review_intel.analysis.confidence import compute_confidence
from review_intel.schemas.analysis import ReviewEvidence
from review_intel.schemas.review import Platform, ReviewSchema
from review_intel.schemas.waba import WABATheme


class TestWABAClassifier:
    @pytest.fixture
    def classifier(self):
        return WABAClassifier()

    def test_broadcast_theme_detected(self, classifier):
        review = ReviewSchema(
            text="The broadcast campaign feature is excellent for bulk messaging to our customers",
            competitor_name="Interakt",
        )
        result = classifier.classify(review)
        assert WABATheme.BROADCAST_CAMPAIGNS in result.themes

    def test_template_approval_detected(self, classifier):
        review = ReviewSchema(
            text="Template approval process takes too long and templates get rejected without clear reasons",
            competitor_name="Wati",
        )
        result = classifier.classify(review)
        assert WABATheme.TEMPLATE_APPROVALS in result.themes

    def test_multiple_themes(self, classifier):
        review = ReviewSchema(
            text="The chatbot builder is decent but the CRM sync with HubSpot integration needs work. "
                 "Also the pricing is too expensive for small teams.",
            competitor_name="Gallabox",
        )
        result = classifier.classify(review)
        assert len(result.themes) >= 2
        assert result.is_waba_relevant

    def test_non_waba_review(self, classifier):
        review = ReviewSchema(
            text="The restaurant had great food and excellent service. Would visit again.",
            competitor_name="SomeRestaurant",
        )
        result = classifier.classify(review)
        assert not result.is_waba_relevant

    def test_batch_classification(self, classifier, sample_reviews):
        results = classifier.classify_batch(sample_reviews)
        assert len(results) == len(sample_reviews)
        waba_count = sum(1 for r in results if r.is_waba_relevant)
        assert waba_count > 0  # At least some reviews should be WABA-relevant

    def test_theme_distribution(self, classifier, sample_reviews):
        results = classifier.classify_batch(sample_reviews)
        dist = classifier.get_theme_distribution(results)
        assert isinstance(dist, dict)


class TestConfidenceScoring:
    def test_high_confidence(self):
        evidence = [
            ReviewEvidence(review_id=f"r{i}", source=Platform.G2, quote="x" * 100)
            for i in range(5)
        ] + [
            ReviewEvidence(review_id=f"c{i}", source=Platform.CAPTERRA, quote="y" * 100)
            for i in range(5)
        ]
        score, factors = compute_confidence(
            review_count=50,
            evidence=evidence,
            sentiment_values=[0.8, 0.9, 0.7, 0.85],
            verified_count=8,
            total_count=10,
        )
        assert score >= 60

    def test_low_confidence(self):
        score, factors = compute_confidence(
            review_count=1,
            evidence=[],
            sentiment_values=[],
        )
        assert score < 30

    def test_factors_breakdown(self):
        evidence = [
            ReviewEvidence(review_id="r1", source=Platform.G2, quote="Evidence text here"),
        ]
        score, factors = compute_confidence(
            review_count=5,
            evidence=evidence,
            sentiment_values=[0.5],
        )
        assert factors.volume_score > 0
        assert factors.total == score
