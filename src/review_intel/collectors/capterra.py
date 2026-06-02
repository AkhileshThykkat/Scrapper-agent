"""
Capterra collector — structured review extraction from Capterra.com.

Extracts: rating, title, pros, cons, reviewer name, role,
company size, date, and review URL.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime

from review_intel.collectors.base import BaseCollector
from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)


class CapterraCollector(BaseCollector):
    """Collect structured reviews from Capterra.com."""

    @property
    def platform(self) -> Platform:
        return Platform.CAPTERRA

    async def collect(
        self,
        company: str,
        max_reviews: int = 200,
        since: datetime | None = None,
    ) -> list[ReviewSchema]:
        try:
            from agent.browser import HumanBrowser
        except ImportError:
            logger.error("agent.browser not available for CapterraCollector")
            return []

        slug = re.sub(r"[^a-z0-9]+", "-", company.lower()).strip("-")
        reviews: list[ReviewSchema] = []

        try:
            async with HumanBrowser(headless=True, slow_mo=30) as browser:
                page_num = 1
                while len(reviews) < max_reviews and page_num <= 10:
                    url = f"https://www.capterra.com/p/{slug}/reviews/?page={page_num}"
                    logger.info("Capterra: fetching %s", url)

                    try:
                        await asyncio.wait_for(
                            browser.page.goto(url, wait_until="domcontentloaded", timeout=25000),
                            timeout=30,
                        )
                        await browser.wait_random(2.0, 4.0)

                        for _ in range(3):
                            await browser.page.evaluate("window.scrollBy(0, 800)")
                            await browser.wait_random(0.5, 1.0)

                        raw_reviews = await asyncio.wait_for(
                            browser.page.evaluate("""() => {
                                const reviews = [];
                                const cards = document.querySelectorAll(
                                    '[class*="review-card"], [class*="ReviewCard"], [itemprop="review"]'
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
                                    const ratingEl = card.querySelector('[class*="overall-rating"], [itemprop="ratingValue"]');
                                    if (ratingEl) {
                                        const m = (ratingEl.textContent || ratingEl.getAttribute('content') || '').match(/(\\d+\\.?\\d*)/);
                                        if (m) rating = m[1];
                                    }

                                    const title = getText('[class*="review-title"], h3, [itemprop="name"]');
                                    const pros = getText('[class*="pros"], [class*="Pros"]');
                                    const cons = getText('[class*="cons"], [class*="Cons"]');
                                    const body = getText('[itemprop="reviewBody"], [class*="review-body"], [class*="ReviewBody"]');
                                    const reviewer = getText('[itemprop="author"], [class*="reviewer-name"]');
                                    const role = getText('[class*="reviewer-title"], [class*="job-title"]');
                                    const company_size = getText('[class*="company-size"]');
                                    const dateStr = getAttr('time, [itemprop="datePublished"]', 'datetime')
                                        || getText('time, [itemprop="datePublished"]');
                                    const verified = !!card.querySelector('[class*="verified"]');

                                    if (body.length > 15 || pros.length > 15) {
                                        reviews.push({
                                            title, rating, pros, cons, body,
                                            reviewer, role, company_size,
                                            date: dateStr, verified
                                        });
                                    }
                                });
                                return reviews;
                            }"""),
                            timeout=10,
                        )

                        if not raw_reviews:
                            break

                        for raw in raw_reviews:
                            if len(reviews) >= max_reviews:
                                break
                            text = raw.get("body", "")
                            if len(text) < 15 and len(raw.get("pros", "")) < 15:
                                continue

                            rating_val = None
                            if raw.get("rating"):
                                try:
                                    rating_val = min(float(raw["rating"]), 5.0)
                                except ValueError:
                                    pass

                            date_val = None
                            if raw.get("date"):
                                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y"):
                                    try:
                                        date_val = datetime.strptime(raw["date"].strip()[:19], fmt)
                                        break
                                    except ValueError:
                                        continue

                            reviews.append(ReviewSchema(
                                text=text or f"Pros: {raw.get('pros', '')} Cons: {raw.get('cons', '')}",
                                title=raw.get("title") or None,
                                pros=raw.get("pros") or None,
                                cons=raw.get("cons") or None,
                                rating=rating_val,
                                date=date_val,
                                reviewer_name=raw.get("reviewer") or None,
                                reviewer_role=raw.get("role") or None,
                                company_size=raw.get("company_size") or None,
                                verified=raw.get("verified", False),
                                platform=Platform.CAPTERRA,
                                competitor_name=company,
                                review_url=url,
                            ))

                        page_num += 1
                        await browser.wait_random(1.5, 3.0)

                    except asyncio.TimeoutError:
                        logger.warning("Capterra: timeout on page %d", page_num)
                        break
                    except Exception as e:
                        logger.warning("Capterra: error on page %d: %s", page_num, e)
                        break

        except Exception as e:
            logger.error("CapterraCollector failed for %s: %s", company, e)

        self._log_collection(company, len(reviews))
        return reviews
