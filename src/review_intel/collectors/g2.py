"""
G2 collector — structured review extraction from G2.com.

Extracts: rating, title, pros, cons, reviewer name, role, company size,
industry, date, verified status, helpful votes, and review URL.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional

from review_intel.collectors.base import BaseCollector
from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)


class G2Collector(BaseCollector):
    """Collect structured reviews from G2.com."""

    @property
    def platform(self) -> Platform:
        return Platform.G2

    async def collect(
        self,
        company: str,
        max_reviews: int = 200,
        since: datetime | None = None,
    ) -> list[ReviewSchema]:
        try:
            from agent.browser import HumanBrowser
        except ImportError:
            logger.error("agent.browser not available for G2Collector")
            return []

        slug = self._make_slug(company)
        reviews: list[ReviewSchema] = []

        try:
            async with HumanBrowser(headless=True, slow_mo=30) as browser:
                page = 1
                while len(reviews) < max_reviews and page <= 10:
                    url = f"https://www.g2.com/products/{slug}/reviews?page={page}"
                    logger.info("G2: fetching %s", url)

                    try:
                        await asyncio.wait_for(
                            browser.page.goto(url, wait_until="domcontentloaded", timeout=25000),
                            timeout=30,
                        )
                        await browser.wait_random(2.0, 4.0)

                        # Scroll to load lazy content
                        for _ in range(3):
                            await browser.page.evaluate("window.scrollBy(0, 800)")
                            await browser.wait_random(0.5, 1.0)

                        # Extract structured review data
                        raw_reviews = await asyncio.wait_for(
                            browser.page.evaluate("""() => {
                                const reviews = [];
                                const cards = document.querySelectorAll('[itemprop="review"], .nested-ajax-loading .paper');
                                cards.forEach(card => {
                                    const getText = (sel) => {
                                        const el = card.querySelector(sel);
                                        return el ? el.textContent.trim() : '';
                                    };
                                    const getAttr = (sel, attr) => {
                                        const el = card.querySelector(sel);
                                        return el ? el.getAttribute(attr) : '';
                                    };

                                    const ratingEl = card.querySelector('[class*="star-rating"] [class*="filled"]') 
                                        || card.querySelector('.stars [aria-label]');
                                    let rating = '';
                                    if (ratingEl) {
                                        const label = ratingEl.getAttribute('aria-label') || ratingEl.className || '';
                                        const match = label.match(/(\\d+\\.?\\d*)/);
                                        if (match) rating = match[1];
                                    }

                                    const title = getText('h3, [itemprop="name"], .review-title');
                                    const pros = getText('[id*="pros"], .pros-cell, .review-pros');
                                    const cons = getText('[id*="cons"], .cons-cell, .review-cons');
                                    const body = getText('[itemprop="reviewBody"], .formatted-text, .review-body');
                                    const reviewer = getText('.mt-4th [itemprop="author"], .reviewer-name, [class*="reviewer"]');
                                    const role = getText('.mt-4th .secondary, .reviewer-title, [class*="job-title"]');
                                    const company_size = getText('[class*="company-size"], [class*="firm-size"]');
                                    const industry = getText('[class*="industry"]');
                                    const dateStr = getAttr('time, [itemprop="datePublished"]', 'datetime') 
                                        || getText('time, [itemprop="datePublished"]');
                                    const verified = !!card.querySelector('[class*="verified"], [class*="Verified"]');
                                    const linkEl = card.querySelector('a[href*="/reviews/"]');
                                    const reviewUrl = linkEl ? linkEl.href : '';

                                    if (body.length > 15 || pros.length > 15) {
                                        reviews.push({
                                            title, rating, pros, cons, body, reviewer,
                                            role, company_size, industry, date: dateStr,
                                            verified, review_url: reviewUrl
                                        });
                                    }
                                });
                                return reviews;
                            }"""),
                            timeout=10,
                        )

                        if not raw_reviews:
                            logger.info("G2: no reviews found on page %d, stopping", page)
                            break

                        for raw in raw_reviews:
                            if len(reviews) >= max_reviews:
                                break
                            text = raw.get("body", "") or ""
                            if len(text) < 15 and len(raw.get("pros", "")) < 15:
                                continue

                            review = ReviewSchema(
                                text=text or f"Pros: {raw.get('pros', '')} Cons: {raw.get('cons', '')}",
                                title=raw.get("title") or None,
                                pros=raw.get("pros") or None,
                                cons=raw.get("cons") or None,
                                rating=self._parse_rating(raw.get("rating", "")),
                                date=self._parse_date(raw.get("date", "")),
                                reviewer_name=raw.get("reviewer") or None,
                                reviewer_role=raw.get("role") or None,
                                company_size=raw.get("company_size") or None,
                                industry=raw.get("industry") or None,
                                verified=raw.get("verified", False),
                                platform=Platform.G2,
                                competitor_name=company,
                                review_url=raw.get("review_url") or f"https://www.g2.com/products/{slug}/reviews",
                            )
                            reviews.append(review)

                        page += 1
                        await browser.wait_random(1.5, 3.0)

                    except asyncio.TimeoutError:
                        logger.warning("G2: timeout on page %d", page)
                        break
                    except Exception as e:
                        logger.warning("G2: error on page %d: %s", page, e)
                        break

        except Exception as e:
            logger.error("G2Collector failed for %s: %s", company, e)

        self._log_collection(company, len(reviews))
        return reviews

    @staticmethod
    def _make_slug(name: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    @staticmethod
    def _parse_rating(val: str) -> float | None:
        if not val:
            return None
        try:
            r = float(val)
            return min(max(r, 0), 5)
        except ValueError:
            return None

    @staticmethod
    def _parse_date(val: str) -> datetime | None:
        if not val:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(val.strip()[:19], fmt)
            except ValueError:
                continue
        return None
