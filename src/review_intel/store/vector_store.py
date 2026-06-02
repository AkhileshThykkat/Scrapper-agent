"""
ChromaDB vector store implementation.

Wraps ChromaDB with the VectorStore protocol, adding proper metadata handling
and batch operations for ReviewSchema objects.
"""

from __future__ import annotations

import logging
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

from review_intel.schemas.review import ReviewSchema

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """Vector store backed by ChromaDB with sentence-transformer embeddings."""

    def __init__(
        self,
        collection_name: str = "reviews",
        persist_dir: str = "./chroma_data",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self._model = SentenceTransformer(model_name)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaVectorStore initialized: collection=%s, persist=%s",
            collection_name, persist_dir,
        )

    def index_reviews(self, reviews: list[ReviewSchema], company: str) -> int:
        """Index reviews into ChromaDB with full metadata."""
        texts: list[str] = []
        metadatas: list[dict] = []
        ids: list[str] = []

        for review in reviews:
            text = review.full_text.strip()
            if not text or len(text) < 20:
                continue

            texts.append(text)
            metadatas.append({
                "company": company,
                "platform": review.platform.value,
                "rating": str(review.rating) if review.rating is not None else "",
                "reviewer": review.reviewer_name or "",
                "reviewer_role": review.reviewer_role or "",
                "date": review.date.isoformat() if review.date else "",
                "verified": str(review.verified),
                "country": review.country or "",
                "quality_score": str(review.quality_score) if review.quality_score is not None else "",
                "review_url": review.review_url or "",
            })
            ids.append(review.id)

        if not texts:
            return 0

        # Batch encode and upsert
        embeddings = self._model.encode(texts, show_progress_bar=False).tolist()
        batch_size = 500
        indexed = 0
        for i in range(0, len(texts), batch_size):
            end = min(i + batch_size, len(texts))
            self._collection.upsert(
                embeddings=embeddings[i:end],
                documents=texts[i:end],
                metadatas=metadatas[i:end],
                ids=ids[i:end],
            )
            indexed += end - i

        logger.info("Indexed %d reviews for %s", indexed, company)
        return indexed

    def search(
        self,
        query: str,
        company: Optional[str] = None,
        n_results: int = 20,
    ) -> list[dict]:
        """Semantic search over indexed reviews."""
        query_embedding = self._model.encode([query]).tolist()
        where = {"company": company} if company else None

        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where,
        )

        output = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                output.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "id": results["ids"][0][i] if results["ids"] else "",
                })
        return output

    def get_all_reviews(self, company: str) -> list[str]:
        """Retrieve all review texts for a company."""
        results = self._collection.get(where={"company": company})
        return results.get("documents", []) if results else []

    def clear_company(self, company: str) -> None:
        """Remove all reviews for a company."""
        try:
            self._collection.delete(where={"company": company})
            logger.info("Cleared reviews for %s", company)
        except Exception as e:
            logger.warning("Failed to clear reviews for %s: %s", company, e)

    def count(self, company: Optional[str] = None) -> int:
        """Count indexed reviews."""
        if company:
            results = self._collection.get(where={"company": company})
            return len(results.get("ids", [])) if results else 0
        return self._collection.count()

    def get_companies(self) -> list[str]:
        """List all companies with indexed reviews."""
        all_data = self._collection.get()
        companies: set[str] = set()
        if all_data and all_data.get("metadatas"):
            for meta in all_data["metadatas"]:
                if meta and "company" in meta:
                    companies.add(meta["company"])
        return sorted(companies)
