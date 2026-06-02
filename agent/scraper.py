import asyncio
import logging
import re
from typing import List, Optional
from urllib.parse import quote

from agent.browser import HumanBrowser

logger = logging.getLogger(__name__)

DEFAULT_MAX_REVIEWS = 200

NOISE_PATTERNS = [
    r"people also ask",
    r"an error has occurred",
    r"please try again later",
    r"who is the founder",
    r"is\s+\w+\s+(a\s+)?(good|bad)\s+company",
    r"share more feedback",
    r"report a problem",
    r"close\s*$",
    r"^\s*$",
    r"feedback\s*$",
    r"ad\s*$",
    r"sponsored",
    r"sign in",
    r"create account",
    r"terms of service",
    r"privacy policy",
    r"cookie",
    r"settings",
    r"search",
    r"results",
    r"read more",
    r"see more",
    r"was this (summary|helpful|review)",
    r"what people talk about",
    r"what are some problems",
    r"in this guide",
    r"you'll learn",
    r"bringing the customer back",
    r"more reviews",
]


def _is_noise(text: str) -> bool:
    text_lower = text.lower().strip()
    if len(text_lower) < 25:
        return True
    for pat in NOISE_PATTERNS:
        if re.search(pat, text_lower):
            return True
    return False


def _is_review_like(text: str) -> bool:
    """Heuristic: real reviews mention specific product aspects."""
    review_indicators = [
        "app", "platform", "feature", "bot", "chat", "message", "campaign",
        "broadcast", "template", "dashboard", "analytics", "report", "contact",
        "lead", "customer", "support", "team", "account", "billing", "price",
        "integration", "api", "webhook", "notification", "response", "speed",
        "update", "version", "interface", "design", "easy", "difficult",
        "confusing", "crash", "slow", "bug", "fix", "working", "broken",
        "recommend", "love", "hate", "terrible", "amazing", "awesome",
        "helpful", "frustrat", "waste", "worth", "money", "expensive",
        "afford", "setup", "onboard", "tutorial", "guide", "documentation",
        "whatsapp", "sms", "email", "crm", "pipedrive", "hubspot",
    ]
    text_lower = text.lower()
    return any(ind in text_lower for ind in review_indicators)


async def _extract_reviews_from_page(browser: HumanBrowser) -> List[str]:
    """Extract review-like text from current page, filtering noise."""
    try:
        texts = await asyncio.wait_for(
            browser.page.evaluate("""
                () => {
                    const selectors = [
                        '.VwiC3b', '.lEBKkf', '.jJc9Ad', '.st',
                        '.g .BNeawe', '.iRPxbe', '.MjjYud .BNeawe',
                        '.hgKElc', '.kno-rdesc span', '.LGOjhe',
                        '.dDoNo', '.G1Rrqc', '.s3v9rd',
                        '.LPtGv', '[data-sncf]',
                        'span[jsname]', '.ujudUb', '.WZ8Tjf',
                        '.zBAuLc', '.HwtpBd',
                        '.BNeawe.deIKCb', '.BNeawe.s3v9rd', '.BNeawe.AP7lnd',
                        'div[data-content-featured]',
                        'div[data-content]',
                    ];
                    const seen = new Set();
                    const out = [];
                    selectors.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            const t = (el.textContent || '').trim();
                            if (t.length > 20 && !seen.has(t)) {
                                seen.add(t);
                                out.push(t);
                            }
                        });
                    });
                    return out;
                }
            """),
            timeout=8,
        )
        filtered = [t for t in texts if not _is_noise(t)]
        return filtered
    except Exception as e:
        logger.warning(f"Extract failed: {e}")
        return []


async def _fallback_extract(browser: HumanBrowser) -> List[str]:
    """Fallback: grab visible text, filter aggressively."""
    try:
        texts = await asyncio.wait_for(
            browser.page.evaluate("""
                () => {
                    const els = document.querySelectorAll('p, q, blockquote, li');
                    const seen = new Set();
                    const out = [];
                    els.forEach(el => {
                        const t = (el.textContent || '').trim();
                        if (t.length > 30 && !seen.has(t)) {
                            seen.add(t);
                            out.push(t);
                        }
                    });
                    return out;
                }
            """),
            timeout=8,
        )
        return [t for t in texts if not _is_noise(t) and _is_review_like(t)]
    except Exception:
        return []


async def _scrape_single_query(browser: HumanBrowser, url: str) -> List[dict]:
    """Run a single Google search and extract review-like text."""
    results = []
    seen = set()

    try:
        await asyncio.wait_for(
            browser.page.goto(url, wait_until="domcontentloaded", timeout=20000),
            timeout=25,
        )
        await browser.wait_random(1.0, 2.0)

        for _ in range(3):
            try:
                await asyncio.wait_for(
                    browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)"),
                    timeout=4,
                )
                await browser.wait_random(0.3, 0.7)
            except Exception:
                break

        texts = await _extract_reviews_from_page(browser)
        if not texts:
            texts = await _fallback_extract(browser)

        for t in texts:
            if t not in seen and _is_review_like(t):
                seen.add(t)
                results.append({"text": t, "source": "google_search"})

        if not results:
            logger.warning(f"No review text found in: {url[:80]}")
    except asyncio.TimeoutError:
        logger.warning(f"Timeout: {url[:60]}")
    except Exception as e:
        logger.warning(f"Query failed: {e}")

    return results


async def scrape_google_reviews(browser: HumanBrowser, company: str, max_reviews: int = DEFAULT_MAX_REVIEWS) -> List[dict]:
    """Scrape reviews via multiple Google search queries."""
    if not browser.page:
        return []

    all_reviews = []
    encoded = quote(company)
    seen_texts = set()

    queries = [
        f"https://www.google.com/search?q={encoded}+reviews",
        f"https://www.google.com/search?q={encoded}+customer+reviews",
        f"https://www.google.com/search?q={encoded}+rating+experience",
        f"https://www.google.com/search?q={encoded}+customer+feedback",
        f"https://www.google.com/search?q={encoded}+problems+issues+complaints",
        f"https://www.google.com/search?q={encoded}+testimonials",
        f"https://www.google.com/search?q={encoded}+is+it+good",
        f"https://www.google.com/search?q=site:trustpilot.com+{encoded}",
        f"https://www.google.com/search?q=site:g2.com+{encoded}+reviews",
        f"https://www.google.com/search?q=site:capterra.com+{encoded}",
        f"https://www.google.com/search?q=site:reddit.com+{encoded}+review",
    ]

    for query in queries:
        if len(all_reviews) >= max_reviews:
            break
        batch = await _scrape_single_query(browser, query)
        for item in batch:
            if item["text"] not in seen_texts and _is_review_like(item["text"]):
                seen_texts.add(item["text"])
                all_reviews.append(item)

    logger.info(f"Got {len(all_reviews)} review items for {company}")
    return all_reviews[:max_reviews]


async def scrape_generic_reviews(browser: HumanBrowser, url: str, max_reviews: int = DEFAULT_MAX_REVIEWS) -> List[dict]:
    """Scrape reviews from a generic review site URL."""
    if not browser.page:
        return []
    reviews = []
    seen = set()

    try:
        await asyncio.wait_for(
            browser.page.goto(url, wait_until="domcontentloaded", timeout=25000),
            timeout=30,
        )
        await browser.wait_random(1.5, 3.0)

        for _ in range(4):
            try:
                await asyncio.wait_for(
                    browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)"),
                    timeout=4,
                )
                await browser.wait_random(0.5, 1.0)
            except Exception:
                break

            raw_texts = await asyncio.wait_for(
                browser.page.evaluate("""
                    () => {
                        const candidates = document.querySelectorAll(
                            'p, .review-text, .review-content, [class*="review"], [class*="Review"], [data-testid*="review"], [itemprop="reviewBody"], q, blockquote'
                        );
                        const seen = new Set();
                        const out = [];
                        candidates.forEach(el => {
                            const t = (el.textContent || '').trim();
                            if (t.length > 20 && t.length < 3000 && !seen.has(t)) {
                                seen.add(t);
                                out.push(t);
                            }
                        });
                        return out;
                    }
                """),
                timeout=8,
            )
            for t in raw_texts:
                if t not in seen and not _is_noise(t):
                    seen.add(t)
                    reviews.append({"text": t, "source": url})

            try:
                next_clicks = [
                    '[aria-label*="Next"]', '[aria-label*="next"]',
                    'a:has-text("Next")', 'button:has-text("Next")',
                    '.pagination .next', '.pagination__next',
                    '.next-page', '.load-more', '.see-more',
                    '[aria-label*="Load more"]',
                ]
                clicked = False
                for btn_sel in next_clicks:
                    try:
                        locator = browser.page.locator(btn_sel).first
                        if await locator.count() > 0 and await locator.is_visible():
                            await locator.click(timeout=3000)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    break
                await browser.wait_random(1.0, 2.0)
            except Exception:
                break

    except asyncio.TimeoutError:
        logger.warning(f"Generic scrape timed out for {url}")
    except Exception as e:
        logger.warning(f"Failed to scrape {url}: {e}")

    return reviews


REVIEW_SITE_TEMPLATES = [
    "https://www.trustpilot.com/review/{domain}",
    "https://www.g2.com/products/{slug}/reviews",
    "https://www.capterra.com/p/{slug}/reviews",
    "https://www.sitejabber.com/reviews/{domain}",
    "https://www.glassdoor.com/Reviews/{slug}-reviews",
]


def _company_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug


def _company_domain(name: str) -> str:
    slug = _company_slug(name)
    return f"{slug}.com"


def _is_google_captcha(url: str) -> bool:
    return "sorry/index" in url or "captcha" in url


SITE_SELECTORS = {
    "trustpilot": [
        'section[class*="review"] p',
        '[data-service-review-text-typography]',
        '.review-content__text',
        'p[class*="typography_body"]',
    ],
    "g2": [
        '[class*="paper"] blockquote',
        '[class*="review"] blockquote',
        '[itemprop="reviewBody"]',
        '[data-testid*="review"] p',
        'p[class*="review"]',
    ],
    "capterra": [
        '[class*="review-body"]',
        '[class*="review-text"]',
        '[itemprop="reviewBody"]',
        '.review-content',
        'p[class*="review"]',
    ],
    "sitejabber": [
        '.review__text',
        '[class*="reviewContent"]',
        '.review-text',
        'p[class*="review"]',
    ],
    "glassdoor": [
        '[class*="reviewText"]',
        '[class*="review"] p',
        '.empReview p',
        'p[class*="review"]',
    ],
    "generic": [
        'p, .review-text, .review-content, [class*="review"], [class*="Review"], '
        '[data-testid*="review"], [itemprop="reviewBody"], q, blockquote, '
        '[class*="feedback"], [class*="testimonial"]',
    ],
}


async def _scrape_known_site(browser: HumanBrowser, url: str, max_reviews: int = 200) -> List[dict]:
    """Scrape reviews from a known review site with site-specific selectors."""
    site_key = "generic"
    for key in ["trustpilot", "g2", "capterra", "sitejabber", "glassdoor"]:
        if key in url.lower():
            site_key = key
            break

    selectors = SITE_SELECTORS[site_key]
    reviews = []
    seen = set()

    try:
        await asyncio.wait_for(
            browser.page.goto(url, wait_until="domcontentloaded", timeout=25000),
            timeout=30,
        )
        await browser.wait_random(2.0, 4.0)

        for _ in range(5):
            try:
                await asyncio.wait_for(
                    browser.page.evaluate("window.scrollTo(0, document.body.scrollHeight)"),
                    timeout=4,
                )
                await browser.wait_random(0.5, 1.5)
            except Exception:
                break

            for sel in selectors:
                try:
                    texts = await asyncio.wait_for(
                        browser.page.evaluate(f"""
                            () => {{
                                const els = document.querySelectorAll('{sel}');
                                const seen = new Set();
                                const out = [];
                                els.forEach(el => {{
                                    const t = (el.textContent || '').trim();
                                    if (t.length > 20 && t.length < 3000 && !seen.has(t)) {{
                                        seen.add(t);
                                        out.push(t);
                                    }}
                                }});
                                return out;
                            }}
                        """),
                        timeout=8,
                    )
                    for t in texts:
                        if t not in seen and not _is_noise(t):
                            seen.add(t)
                            reviews.append({"text": t, "source": url})
                except Exception:
                    continue

            if len(reviews) >= max_reviews:
                break

            try:
                next_btns = [
                    '[aria-label*="Next"]', '[aria-label*="next"]',
                    'a:has-text("Next")', 'button:has-text("Next")',
                    '.pagination .next', '.pagination__next',
                    '.next-page', '.load-more', '.see-more',
                    '[aria-label*="Load more"]',
                ]
                clicked = False
                for btn_sel in next_btns:
                    try:
                        locator = browser.page.locator(btn_sel).first
                        if await locator.count() > 0 and await locator.is_visible():
                            await locator.click(timeout=3000)
                            clicked = True
                            break
                    except Exception:
                        continue
                if clicked:
                    await browser.wait_random(1.0, 2.0)
                else:
                    break
            except Exception:
                break

    except asyncio.TimeoutError:
        logger.warning(f"Known site timed out: {url[:60]}")
    except Exception as e:
        logger.warning(f"Known site failed: {url[:60]}: {e}")

    return reviews


async def scrape_reviews(company: str, extra_sites: Optional[List[str]] = None, max_reviews: int = DEFAULT_MAX_REVIEWS) -> List[dict]:
    """Main entry point to scrape reviews for a company."""
    all_reviews = []
    google_blocked = False
    try:
        async with HumanBrowser(headless=True, slow_mo=20) as browser:
            google_reviews = await asyncio.wait_for(
                scrape_google_reviews(browser, company, max_reviews),
                timeout=max(120, max_reviews),
            )
            all_reviews.extend(google_reviews)

            if browser.page and _is_google_captcha(browser.page.url):
                google_blocked = True
                logger.warning("Google CAPTCHA detected, skipping Google results")

            if extra_sites:
                for site in extra_sites:
                    site = site.strip()
                    if site and site.startswith("http"):
                        site_reviews = await asyncio.wait_for(
                            scrape_generic_reviews(browser, site, max_reviews),
                            timeout=60,
                        )
                        all_reviews.extend(site_reviews)

            need = max_reviews - len(all_reviews)
            if need > 0 or google_blocked:
                slug = _company_slug(company)
                domain = _company_domain(company)
                for template in REVIEW_SITE_TEMPLATES:
                    if len(all_reviews) >= max_reviews:
                        break
                    url = template.format(domain=domain, slug=slug)
                    logger.info(f"Trying known review site: {url}")
                    site_reviews = await asyncio.wait_for(
                        _scrape_known_site(browser, url, max_reviews - len(all_reviews)),
                        timeout=45,
                    )
                    all_reviews.extend(site_reviews)
                    logger.info(f"Got {len(site_reviews)} reviews from {url[:60]}")
    except asyncio.TimeoutError:
        logger.warning(f"Overall scraping timed out for {company}")
    except Exception as e:
        logger.warning(f"Browser/scrape failed for {company}: {e}")

    filtered = [r for r in all_reviews if not _is_noise(r.get("text", "")) and _is_review_like(r.get("text", ""))]
    if not filtered:
        logger.warning(f"No valid reviews found for {company}")
    else:
        logger.info(f"Total valid reviews for {company}: {len(filtered)}")

    return filtered[:max_reviews]
