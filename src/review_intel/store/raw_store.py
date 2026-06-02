"""
SQLite-based raw review storage.

Persists full ReviewSchema objects so scraped data is never lost.
Supports async operations via aiosqlite.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS reviews (
    id TEXT PRIMARY KEY,
    platform_review_id TEXT,
    text TEXT NOT NULL,
    title TEXT,
    pros TEXT,
    cons TEXT,
    rating REAL,
    date TEXT,
    collected_at TEXT NOT NULL,
    reviewer_name TEXT,
    reviewer_role TEXT,
    company_size TEXT,
    industry TEXT,
    country TEXT,
    verified INTEGER DEFAULT 0,
    helpful_votes INTEGER DEFAULT 0,
    platform TEXT NOT NULL,
    review_url TEXT,
    competitor_name TEXT NOT NULL,
    product_category TEXT,
    quality_score REAL,
    language TEXT,
    is_duplicate INTEGER DEFAULT 0,
    is_spam INTEGER DEFAULT 0,
    raw_json TEXT
);
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_reviews_competitor ON reviews(competitor_name);
"""


class SQLiteRawStore:
    """Async SQLite store for raw review persistence."""

    def __init__(self, db_path: str = "./data/reviews.db"):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(_CREATE_TABLE)
            await db.execute(_CREATE_INDEX)
            await db.commit()
        self._initialized = True
        logger.info("SQLiteRawStore initialized at %s", self._db_path)

    async def save_reviews(self, reviews: list[ReviewSchema]) -> int:
        await self._ensure_initialized()
        saved = 0
        async with aiosqlite.connect(self._db_path) as db:
            for review in reviews:
                try:
                    await db.execute(
                        """INSERT OR REPLACE INTO reviews
                        (id, platform_review_id, text, title, pros, cons, rating,
                         date, collected_at, reviewer_name, reviewer_role,
                         company_size, industry, country, verified, helpful_votes,
                         platform, review_url, competitor_name, product_category,
                         quality_score, language, is_duplicate, is_spam, raw_json)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            review.id,
                            review.platform_review_id,
                            review.text,
                            review.title,
                            review.pros,
                            review.cons,
                            review.rating,
                            review.date.isoformat() if review.date else None,
                            review.collected_at.isoformat(),
                            review.reviewer_name,
                            review.reviewer_role,
                            review.company_size,
                            review.industry,
                            review.country,
                            int(review.verified),
                            review.helpful_votes,
                            review.platform.value,
                            review.review_url,
                            review.competitor_name,
                            review.product_category,
                            review.quality_score,
                            review.language,
                            int(review.is_duplicate),
                            int(review.is_spam),
                            review.model_dump_json(exclude={"raw_html"}),
                        ),
                    )
                    saved += 1
                except Exception as e:
                    logger.warning("Failed to save review %s: %s", review.id, e)
            await db.commit()
        logger.info("Saved %d/%d reviews to raw store", saved, len(reviews))
        return saved

    async def get_reviews(
        self, company: str, limit: int = 1000, offset: int = 0,
    ) -> list[ReviewSchema]:
        await self._ensure_initialized()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT raw_json FROM reviews WHERE competitor_name = ? LIMIT ? OFFSET ?",
                (company, limit, offset),
            )
            rows = await cursor.fetchall()
        return [ReviewSchema.model_validate_json(row["raw_json"]) for row in rows]

    async def get_review_by_id(self, review_id: str) -> ReviewSchema | None:
        await self._ensure_initialized()
        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT raw_json FROM reviews WHERE id = ?", (review_id,),
            )
            row = await cursor.fetchone()
        if row:
            return ReviewSchema.model_validate_json(row["raw_json"])
        return None

    async def get_companies(self) -> list[str]:
        await self._ensure_initialized()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT DISTINCT competitor_name FROM reviews ORDER BY competitor_name",
            )
            rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def count(self, company: str | None = None) -> int:
        await self._ensure_initialized()
        async with aiosqlite.connect(self._db_path) as db:
            if company:
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM reviews WHERE competitor_name = ?", (company,),
                )
            else:
                cursor = await db.execute("SELECT COUNT(*) FROM reviews")
            row = await cursor.fetchone()
        return row[0] if row else 0

    async def delete_company(self, company: str) -> int:
        await self._ensure_initialized()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "DELETE FROM reviews WHERE competitor_name = ?", (company,),
            )
            await db.commit()
            return cursor.rowcount
