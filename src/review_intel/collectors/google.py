"""
Google search fallback collector — adapted from the existing scraper.

Uses Google search to find review-like text when direct platform
collectors are unavailable or blocked.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from review_intel.collectors.base import BaseCollector
from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)

# Reuse the noise detection from the original codebase
NOISE_PATTERNS = [
    r"people also ask", r"an error has occurred", r"please try again later",
    r"share more feedback", r"report a problem", r"close\s*$", r"^\s*$",
    r"sponsored", r"sign in", r"create account", r"terms of service",
    r"privacy policy", r"cookie", r"was this (summary|helpful|review)",
    r"what people talk about", r"more reviews",
]

REVIEW_INDICATORS = [
    "app", "platform", "feature", "bot", "chat", "message", "campaign",
    "broadcast", "template", "dashboard", "analytics", "support", "team",
    "billing", "price", "integration", "api", "webhook", "recommend",
    "love", "hate", "terrible", "amazing", "helpful", "frustrat", "waste",
    "worth", "money", "expensive", "setup", "onboard", "whatsapp", "crm",
]


def _is_noise(text: str) -> bool:
    text_lower = text.lower().strip()
    if len(text_lower) < 25:
        return True
    return any(re.search(p, text_lower) for p in NOISE_PATTERNS)


def _is_review_like(text: str) -> bool:
    text_lower = text.lower()
    return any(ind in text_lower for ind in REVIEW_INDICATORS)


class GoogleSearchCollector(BaseCollector):
    """Collect reviews via Google search results."""

    @property
    def platform(self) -> Platform:
        return Platform.GOOGLE

    async def collect(
        self,
        company: str,
        max_reviews: int = 200,
        since: datetime | None = None,
    ) -> list[ReviewSchema]:
        try:
            from agent.browser import HumanBrowser
        except ImportError:
            logger.error("agent.browser not available for GoogleSearchCollector")
            return []

        reviews: list[ReviewSchema] = []
        seen: set[str] = set()
        encoded = quote(company)

        queries = [
            f"https://www.google.com/search?q={encoded}+reviews",
            f"https://www.google.com/search?q={encoded}+customer+reviews",
            f"https://www.google.com/search?q={encoded}+problems+issues+complaints",
            f"https://www.google.com/search?q=site:trustpilot.com+{encoded}",
            f"https://www.google.com/search?q=site:g2.com+{encoded}+reviews",
            f"https://www.google.com/search?q=site:capterra.com+{encoded}",
        ]

        try:
            async with HumanBrowser(headless=True, slow_mo=20) as browser:
                for query_url in queries:
                    if len(reviews) >= max_reviews:
                        break
                    try:
                        await asyncio.wait_for(
                            browser.page.goto(query_url, wait_until="domcontentloaded", timeout=20000),
                            timeout=25,
                        )
                        await browser.wait_random(1.0, 2.0)

                        texts = await asyncio.wait_for(
                            browser.page.evaluate("""() => {
                                const sels = ['.VwiC3b','.lEBKkf','.BNeawe.deIKCb','.BNeawe.s3v9rd','p','blockquote'];
                                const seen = new Set(); const out = [];
                                sels.forEach(s => document.querySelectorAll(s).forEach(el => {
                                    const t = (el.textContent || '').trim();
                                    if (t.length > 20 && !seen.has(t)) { seen.add(t); out.push(t); }
                                }));
                                return out;
                            }"""),
                            timeout=8,
                        )

                        for t in texts:
                            if t not in seen and not _is_noise(t) and _is_review_like(t):
                                seen.add(t)
                                reviews.append(ReviewSchema(
                                    text=t,
                                    platform=Platform.GOOGLE,
                                    competitor_name=company,
                                    review_url=query_url,
                                ))
                    except Exception as e:
                        logger.warning("Google query failed: %s", e)
        except Exception as e:
            logger.error("GoogleSearchCollector failed: %s", e)

        self._log_collection(company, len(reviews))
        return reviews[:max_reviews]
