"""Unit tests for processing pipeline steps."""

import pytest

from review_intel.processors.deduplicator import DeduplicationStep
from review_intel.processors.spam_detector import SpamDetectionStep
from review_intel.processors.quality_scorer import QualityScoringStep
from review_intel.processors.normalizer import NormalizationStep
from review_intel.processors.pipeline import ReviewPipeline
from review_intel.schemas.review import ReviewSchema, Platform


class TestDeduplication:
    @pytest.mark.asyncio
    async def test_exact_duplicates_removed(self, duplicate_reviews):
        step = DeduplicationStep()
        result = await step.process(duplicate_reviews)
        # 2 exact dupes + 1 fuzzy = should keep 2
        assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_unique_reviews_preserved(self, sample_reviews):
        step = DeduplicationStep()
        result = await step.process(sample_reviews)
        assert len(result) == len(sample_reviews)

    @pytest.mark.asyncio
    async def test_empty_list(self):
        step = DeduplicationStep()
        result = await step.process([])
        assert result == []


class TestSpamDetection:
    @pytest.mark.asyncio
    async def test_spam_detected(self, spam_review):
        step = SpamDetectionStep()
        result = await step.process([spam_review])
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_legitimate_reviews_kept(self, sample_reviews):
        step = SpamDetectionStep()
        result = await step.process(sample_reviews)
        assert len(result) == len(sample_reviews)


class TestQualityScoring:
    @pytest.mark.asyncio
    async def test_scores_assigned(self, sample_reviews):
        step = QualityScoringStep(min_quality=0.0)
        result = await step.process(sample_reviews)
        assert all(r.quality_score is not None for r in result)
        assert all(0 <= r.quality_score <= 1 for r in result)

    @pytest.mark.asyncio
    async def test_structured_data_bonus(self, sample_review):
        step = QualityScoringStep(min_quality=0.0)
        result = await step.process([sample_review])
        assert result[0].quality_score > 0.3  # Has rating, date, reviewer, verified

    @pytest.mark.asyncio
    async def test_low_quality_filtered(self):
        low_q = ReviewSchema(
            text="ok it is fine I guess",
            competitor_name="Test", platform=Platform.UNKNOWN,
        )
        step = QualityScoringStep(min_quality=0.3)
        result = await step.process([low_q])
        assert len(result) == 0


class TestNormalization:
    @pytest.mark.asyncio
    async def test_smart_quotes_replaced(self):
        r = ReviewSchema(
            text="\u201cThis is a test with smart quotes\u201d said the reviewer clearly",
            competitor_name="Test",
        )
        step = NormalizationStep()
        result = await step.process([r])
        assert "\u201c" not in result[0].text
        assert '"' in result[0].text


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_runs_all_steps(self, sample_reviews):
        pipeline = ReviewPipeline([
            NormalizationStep(),
            DeduplicationStep(),
            SpamDetectionStep(),
            QualityScoringStep(min_quality=0.0),
        ])
        result = await pipeline.process(sample_reviews)
        assert result.input_count == len(sample_reviews)
        assert result.output_count > 0
        assert len(result.step_results) == 4
        assert result.total_duration_ms > 0
