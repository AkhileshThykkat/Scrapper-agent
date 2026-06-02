"""
Collector registry — factory for creating and combining collectors.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from review_intel.collectors.base import BaseCollector
from review_intel.collectors.google import GoogleSearchCollector
from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)


def get_collector(platform: Platform) -> BaseCollector | None:
    """Get a collector instance for a given platform."""
    match platform:
        case Platform.GOOGLE:
            return GoogleSearchCollector()
        case Platform.G2:
            from review_intel.collectors.g2 import G2Collector
            return G2Collector()
        case Platform.CAPTERRA:
            from review_intel.collectors.capterra import CapterraCollector
            return CapterraCollector()
        case Platform.TRUSTPILOT:
            from review_intel.collectors.trustpilot import TrustpilotCollector
            return TrustpilotCollector()
        case _:
            return None


def get_all_collectors() -> list[BaseCollector]:
    """Get all available collector instances."""
    collectors = []
    for platform in [Platform.G2, Platform.CAPTERRA, Platform.TRUSTPILOT, Platform.GOOGLE]:
        c = get_collector(platform)
        if c:
            collectors.append(c)
    return collectors


async def collect_from_all(
    company: str,
    max_reviews_per_source: int = 100,
    platforms: list[Platform] | None = None,
    max_concurrent: int = 3,
) -> list[ReviewSchema]:
    """
    Collect reviews from multiple platforms concurrently.

    Args:
        company: Company name to search for.
        max_reviews_per_source: Max reviews per platform.
        platforms: Specific platforms to use (None = all).
        max_concurrent: Max concurrent scraping tasks.

    Returns:
        Combined list of reviews from all platforms.
    """
    if platforms:
        collectors = [c for p in platforms if (c := get_collector(p))]
    else:
        collectors = get_all_collectors()

    if not collectors:
        logger.warning("No collectors available")
        return []

    semaphore = asyncio.Semaphore(max_concurrent)
    all_reviews: list[ReviewSchema] = []

    async def _collect_one(collector: BaseCollector) -> list[ReviewSchema]:
        async with semaphore:
            try:
                return await asyncio.wait_for(
                    collector.collect(company, max_reviews=max_reviews_per_source),
                    timeout=300,
                )
            except asyncio.TimeoutError:
                logger.warning("[%s] Collection timed out for %s", collector.platform.value, company)
                return []
            except Exception as e:
                logger.error("[%s] Collection failed for %s: %s", collector.platform.value, company, e)
                return []

    tasks = [_collect_one(c) for c in collectors]
    results = await asyncio.gather(*tasks)

    for result in results:
        all_reviews.extend(result)

    logger.info(
        "Collected %d total reviews for %s from %d platforms",
        len(all_reviews), company, len(collectors),
    )
    return all_reviews
