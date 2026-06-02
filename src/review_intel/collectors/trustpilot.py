"""
Trustpilot collector — structured review extraction from Trustpilot.com.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime

from review_intel.collectors.base import BaseCollector
from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)


class TrustpilotCollector(BaseCollector):
    """Collect structured reviews from Trustpilot.com."""

    @property
    def platform(self) -> Platform:
        return Platform.TRUSTPILOT

    async def collect(
        self,
        company: str,
        max_reviews: int = 200,
        since: datetime | None = None,
    ) -> list[ReviewSchema]:
        try:
            from agent.browser import HumanBrowser
        except ImportError:
            logger.error("agent.browser not available")
            return []

        domain = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-") + ".com"
        reviews: list[ReviewSchema] = []

        try:
            async with HumanBrowser(headless=True, slow_mo=30) as browser:
                page_num = 1
                while len(reviews) < max_reviews and page_num <= 10:
                    url = f"https://www.trustpilot.com/review/{domain}?page={page_num}"
                    logger.info("Trustpilot: fetching %s", url)

                    try:
                        await asyncio.wait_for(
                            browser.page.goto(url, wait_until="domcontentloaded", timeout=25000),
                            timeout=30,
                        )
                        await browser.wait_random(2.0, 4.0)

                        for _ in range(3):
                            await browser.page.evaluate("window.scrollBy(0, 800)")
                            await browser.wait_random(0.5, 1.0)

                        raw = await asyncio.wait_for(
                            browser.page.evaluate("""() => {
                                const reviews = [];
                                const cards = document.querySelectorAll(
                                    '[class*="review-card"], article[class*="review"]'
                                );
                                cards.forEach(card => {
                                    const getText = (sel) => {
                                        const el = card.querySelector(sel);
                                        return el ? el.textContent.trim() : '';
                                    };
                                    const getAttr = (sel, attr) => {
                                        const el = card.querySelector(sel);
                                        return el ? el.getAttribute(attr) : '';
                                    };

                                    let rating = '';
                                    const starEl = card.querySelector('[data-service-review-rating], img[alt*="star"]');
                                    if (starEl) {
                                        const val = starEl.getAttribute('data-service-review-rating')
                                            || (starEl.alt || '').match(/(\\d)/)?.[1] || '';
                                        rating = val;
                                    }

                                    const title = getText('[data-service-review-title-typography], h2');
                                    const body = getText('[data-service-review-text-typography], p[class*="typography"]');
                                    const reviewer = getText('[data-consumer-name-typography], [class*="consumer-name"]');
                                    const dateStr = getAttr('time', 'datetime') || getText('time');
                                    const country = getText('[class*="consumer-location"], [class*="country"]');
                                    const verified = !!card.querySelector('[class*="verified"], [data-verified]');

                                    if (body.length > 15) {
                                        reviews.push({ title, rating, body, reviewer, date: dateStr, country, verified });
                                    }
                                });
                                return reviews;
                            }"""),
                            timeout=10,
                        )

                        if not raw:
                            break

                        for item in raw:
                            if len(reviews) >= max_reviews:
                                break

                            rating_val = None
                            if item.get("rating"):
                                try:
                                    rating_val = min(float(item["rating"]), 5.0)
                                except ValueError:
                                    pass

                            date_val = None
                            if item.get("date"):
                                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
                                    try:
                                        date_val = datetime.strptime(item["date"].strip()[:19], fmt)
                                        break
                                    except ValueError:
                                        continue

                            reviews.append(ReviewSchema(
                                text=item.get("body", ""),
                                title=item.get("title") or None,
                                rating=rating_val,
                                date=date_val,
                                reviewer_name=item.get("reviewer") or None,
                                country=item.get("country") or None,
                                verified=item.get("verified", False),
                                platform=Platform.TRUSTPILOT,
                                competitor_name=company,
                                review_url=url,
                            ))

                        page_num += 1
                        await browser.wait_random(1.5, 3.0)

                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        logger.warning("Trustpilot: error: %s", e)
                        break

        except Exception as e:
            logger.error("TrustpilotCollector failed: %s", e)

        self._log_collection(company, len(reviews))
        return reviews
