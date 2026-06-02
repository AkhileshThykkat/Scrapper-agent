import logging
from typing import List, Optional

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ReviewVectorStore:
    """Vector store for indexing and searching reviews."""

    def __init__(self, collection_name: str = "reviews", persist_dir: str = "./chroma_data"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Vector store initialized with collection '{collection_name}'")

    def index_reviews(self, reviews: List[dict], company: str):
        """Index a list of reviews into the vector store."""
        texts = []
        metadatas = []
        ids = []
        for i, review in enumerate(reviews):
            text = review.get("text", "").strip()
            if not text or len(text) < 20:
                continue
            texts.append(text)
            metadatas.append({
                "company": company,
                "source": review.get("source", "unknown"),
                "rating": review.get("rating", ""),
                "reviewer": review.get("reviewer", ""),
                "date": review.get("date", ""),
            })
            ids.append(f"{company}_{i}")

        if texts:
            embeddings = self.model.encode(texts, show_progress_bar=False).tolist()
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(f"Indexed {len(texts)} reviews for {company}")

    def search_reviews(self, query: str, company: Optional[str] = None, n_results: int = 20) -> List[dict]:
        """Search for reviews similar to the query."""
        query_embedding = self.model.encode([query]).tolist()
        where = {"company": company} if company else None
        results = self.collection.query(
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
                })
        return output

    def get_all_reviews(self, company: str) -> List[str]:
        """Retrieve all review texts for a company."""
        results = self.collection.get(where={"company": company})
        return results.get("documents", []) if results else []

    def clear_company(self, company: str):
        """Remove all reviews for a given company."""
        self.collection.delete(where={"company": company})
        logger.info(f"Cleared reviews for {company}")
