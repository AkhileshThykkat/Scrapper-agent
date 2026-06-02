"""
FastAPI dependency injection — provides shared instances of stores, LLM clients, and pipelines.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from review_intel.analysis.chain import AnalysisChain
from review_intel.analysis.llm.base import BaseLLMClient
from review_intel.analysis.steps.competitive_intel import CompetitiveIntelStep
from review_intel.analysis.steps.executive_summary import ExecutiveSummaryStep
from review_intel.analysis.steps.feature_request_extraction import FeatureRequestExtractionStep
from review_intel.analysis.steps.pain_point_extraction import PainPointExtractionStep
from review_intel.analysis.steps.raw_extraction import RawExtractionStep
from review_intel.analysis.steps.theme_extraction import ThemeExtractionStep
from review_intel.config import LLMProvider, get_settings
from review_intel.processors.deduplicator import DeduplicationStep
from review_intel.processors.normalizer import NormalizationStep
from review_intel.processors.pipeline import ReviewPipeline
from review_intel.processors.quality_scorer import QualityScoringStep
from review_intel.processors.spam_detector import SpamDetectionStep
from review_intel.store.cache import AnalysisCache
from review_intel.store.raw_store import SQLiteRawStore
from review_intel.store.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_vector_store() -> ChromaVectorStore:
    settings = get_settings()
    return ChromaVectorStore(persist_dir=settings.chroma_persist_dir)


@lru_cache(maxsize=1)
def get_raw_store() -> SQLiteRawStore:
    settings = get_settings()
    return SQLiteRawStore(db_path=settings.raw_store_path)


@lru_cache(maxsize=1)
def get_cache() -> AnalysisCache:
    settings = get_settings()
    return AnalysisCache(max_size=settings.cache_max_size, ttl_seconds=settings.cache_ttl_seconds)


@lru_cache(maxsize=1)
def get_llm_client() -> BaseLLMClient | None:
    """Create the appropriate LLM client based on configuration."""
    settings = get_settings()
    match settings.active_llm_provider:
        case LLMProvider.OLLAMA:
            from review_intel.analysis.llm.ollama_client import OllamaClient
            return OllamaClient(settings.ollama_base_url, settings.local_model)
        case LLMProvider.ANTHROPIC:
            from review_intel.analysis.llm.anthropic_client import AnthropicClient
            return AnthropicClient(settings.anthropic_api_key, settings.anthropic_model)
        case LLMProvider.OPENAI:
            from review_intel.analysis.llm.openai_client import OpenAIClient
            return OpenAIClient(settings.openai_api_key, settings.openai_model)
        case LLMProvider.NONE:
            logger.warning("No LLM configured — analysis will use keyword-based fallback")
            return None


def get_processing_pipeline() -> ReviewPipeline:
    """Build the default processing pipeline."""
    return ReviewPipeline([
        NormalizationStep(),
        DeduplicationStep(),
        SpamDetectionStep(),
        QualityScoringStep(min_quality=0.15),
    ])


def get_analysis_chain() -> AnalysisChain | None:
    """Build the multi-step analysis chain."""
    llm = get_llm_client()
    if not llm:
        return None
    return AnalysisChain(llm=llm, steps=[
        RawExtractionStep(llm),
        ThemeExtractionStep(llm),
        PainPointExtractionStep(llm),
        FeatureRequestExtractionStep(llm),
        CompetitiveIntelStep(llm),
        ExecutiveSummaryStep(llm),
    ])
