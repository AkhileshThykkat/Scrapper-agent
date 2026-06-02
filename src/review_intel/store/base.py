"""
Abstract store protocols.

All store implementations must conform to these protocols,
enabling swappable backends and dependency injection.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from review_intel.schemas.review import ReviewSchema


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector similarity search over reviews."""

    def index_reviews(self, reviews: list[ReviewSchema], company: str) -> int:
        """Index reviews and return count indexed."""
        ...

    def search(self, query: str, company: str | None = None, n_results: int = 20) -> list[dict]:
        """Search for reviews similar to query. Returns list of {text, metadata, distance}."""
        ...

    def get_all_reviews(self, company: str) -> list[str]:
        """Retrieve all review texts for a company."""
        ...

    def clear_company(self, company: str) -> None:
        """Remove all reviews for a company."""
        ...

    def count(self, company: str | None = None) -> int:
        """Count indexed reviews, optionally filtered by company."""
        ...


@runtime_checkable
class RawStore(Protocol):
    """Protocol for persistent raw review storage."""

    async def save_reviews(self, reviews: list[ReviewSchema]) -> int:
        """Persist reviews and return count saved."""
        ...

    async def get_reviews(
        self, company: str, limit: int = 1000, offset: int = 0,
    ) -> list[ReviewSchema]:
        """Retrieve reviews for a company."""
        ...

    async def get_review_by_id(self, review_id: str) -> ReviewSchema | None:
        """Retrieve a single review by ID."""
        ...

    async def get_companies(self) -> list[str]:
        """List all companies with stored reviews."""
        ...

    async def count(self, company: str | None = None) -> int:
        """Count stored reviews."""
        ...

    async def delete_company(self, company: str) -> int:
        """Delete all reviews for a company. Returns count deleted."""
        ...
