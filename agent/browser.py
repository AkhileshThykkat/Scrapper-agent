import asyncio
import logging
import random
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
]


class HumanBrowser:
    """Browser automation with human-like behavior patterns."""

    def __init__(self, headless: bool = False, slow_mo: int = 50):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def start(self):
        self._playwright = await async_playwright().start()
        user_agent = random.choice(USER_AGENTS)
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": random.randint(1200, 1400), "height": random.randint(800, 900)},
            locale="en-US",
            timezone_id="America/New_York",
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)
        self.page = await context.new_page()
        logger.info("Browser started with human-like fingerprint")

    async def human_scroll(self, pauses: int = 3):
        if not self.page:
            return
        for _ in range(pauses):
            scroll_amount = random.randint(300, 700)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await asyncio.sleep(random.uniform(0.8, 2.5))

    async def human_type(self, text: str, selector: str):
        if not self.page:
            return
        await self.page.click(selector)
        await asyncio.sleep(random.uniform(0.3, 0.8))
        for char in text:
            await self.page.type(selector, char, delay=random.randint(30, 120))

    async def human_click(self, selector: str):
        if not self.page:
            return
        await self.page.wait_for_selector(selector, timeout=10000)
        await asyncio.sleep(random.uniform(0.3, 1.2))
        box = await self.page.locator(selector).bounding_box()
        if box:
            x = box["x"] + box["width"] * random.uniform(0.2, 0.8)
            y = box["y"] + box["height"] * random.uniform(0.2, 0.8)
            await self.page.mouse.move(x, y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.1, 0.3))
            await self.page.mouse.click(x, y)
        else:
            await self.page.click(selector)

    async def wait_random(self, min_s: float = 0.5, max_s: float = 2.0):
        await asyncio.sleep(random.uniform(min_s, max_s))

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()
