"""
Abstract base collector — all platform collectors must implement this.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Protocol for platform-specific review collectors."""

    @property
    @abstractmethod
    def platform(self) -> Platform:
        ...

    @abstractmethod
    async def collect(
        self,
        company: str,
        max_reviews: int = 200,
        since: datetime | None = None,
    ) -> list[ReviewSchema]:
        """Collect reviews for a company. Returns normalized ReviewSchema list."""
        ...

    async def health_check(self) -> bool:
        """Check if the collector's target platform is accessible."""
        return True

    def _log_collection(self, company: str, count: int) -> None:
        logger.info(
            "[%s] Collected %d reviews for %s",
            self.platform.value, count, company,
        )
