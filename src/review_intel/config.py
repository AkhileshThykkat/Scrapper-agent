"""
Centralized configuration using pydantic-settings.

All settings are loaded from environment variables with sensible defaults.
Use a .env file or export variables directly.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    NONE = "none"


class VectorStoreBackend(str, Enum):
    """Supported vector store backends."""
    CHROMADB = "chromadb"
    QDRANT = "qdrant"


class Settings(BaseSettings):
    """Application-wide settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM Configuration ──
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    ollama_base_url: str = ""
    local_model: str = "gemma3:12b"

    # ── Vector Store ──
    vector_store_backend: VectorStoreBackend = VectorStoreBackend.CHROMADB
    chroma_persist_dir: str = str(PROJECT_ROOT / "chroma_data")
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "reviews"

    # ── Raw Store ──
    raw_store_path: str = str(PROJECT_ROOT / "data" / "reviews.db")

    # ── Scraping ──
    default_max_reviews: int = 200
    browser_headless: bool = True
    browser_slow_mo: int = 20
    max_concurrent_scrapes: int = 3
    scrape_timeout_seconds: int = 300
    request_delay_min: float = 1.0
    request_delay_max: float = 3.0

    # ── Analysis ──
    max_concurrent_llm_calls: int = 3
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1
    analysis_chunk_size: int = 40
    confidence_min_reviews: int = 3
    confidence_min_sources: int = 2

    # ── Cache ──
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 256

    # ── Logging ──
    log_level: str = "INFO"

    # ── Server ──
    host: str = "0.0.0.0"
    port: int = 8000

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @property
    def active_llm_provider(self) -> LLMProvider:
        """Determine which LLM provider is configured and available."""
        if self.ollama_base_url:
            return LLMProvider.OLLAMA
        if self.anthropic_api_key:
            return LLMProvider.ANTHROPIC
        if self.openai_api_key:
            return LLMProvider.OPENAI
        return LLMProvider.NONE

    @property
    def llm_configured(self) -> bool:
        return self.active_llm_provider != LLMProvider.NONE

    @property
    def active_llm_description(self) -> str:
        """Human-readable description of the active LLM."""
        match self.active_llm_provider:
            case LLMProvider.OLLAMA:
                return f"Ollama ({self.local_model})"
            case LLMProvider.ANTHROPIC:
                return f"Anthropic ({self.anthropic_model})"
            case LLMProvider.OPENAI:
                return f"OpenAI ({self.openai_model})"
            case LLMProvider.NONE:
                return "None (keyword-based fallback)"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    settings = Settings()
    logger.info(
        "Settings loaded: LLM=%s, VectorStore=%s",
        settings.active_llm_description,
        settings.vector_store_backend.value,
    )
    return settings
