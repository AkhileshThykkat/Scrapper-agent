import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent.scraper import scrape_reviews
from agent.embeddings import ReviewVectorStore
from agent.analyzer import analyze_reviews, search_based_analysis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reviews"])
store = ReviewVectorStore()


class ScrapeRequest(BaseModel):
    companies: List[str]
    extra_sites: Optional[List[str]] = None


class AnalyzeRequest(BaseModel):
    company: str


@router.post("/scrape")
async def scrape_endpoint(request: ScrapeRequest):
    """Scrape reviews for given companies."""
    results = {}
    for company in request.companies:
        logger.info(f"Starting scrape for {company}")
        try:
            reviews = await scrape_reviews(company, request.extra_sites)
            if reviews:
                store.index_reviews(reviews, company)
            results[company] = {"count": len(reviews), "status": "success"}
        except Exception as e:
            logger.exception(f"Scraping failed for {company}")
            results[company] = {"count": 0, "status": f"error: {str(e)}"}
    return {"results": results}


@router.post("/analyze/{company}")
async def analyze_endpoint(company: str):
    """Analyze reviews for a specific company."""
    reviews = store.get_all_reviews(company)
    if not reviews:
        raise HTTPException(status_code=404, detail=f"No reviews found for {company}")

    report = analyze_reviews(reviews, company)
    return {"company": company, "report": report, "review_count": len(reviews)}


@router.post("/analyze-semantic/{company}")
async def analyze_semantic_endpoint(company: str):
    """Analyze reviews using semantic search."""
    reviews = store.get_all_reviews(company)
    if not reviews:
        raise HTTPException(status_code=404, detail=f"No reviews found for {company}")

    report = search_based_analysis(store, company)
    return {"company": company, "report": report, "review_count": len(reviews)}


@router.get("/status/{company}")
async def status_endpoint(company: str):
    """Check how many reviews are indexed for a company."""
    reviews = store.get_all_reviews(company)
    return {"company": company, "review_count": len(reviews)}


@router.delete("/clear/{company}")
async def clear_endpoint(company: str):
    """Clear reviews for a company."""
    store.clear_company(company)
    return {"status": "cleared", "company": company}
