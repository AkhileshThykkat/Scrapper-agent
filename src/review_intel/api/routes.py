"""API routes for review intelligence platform."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from review_intel.api.dependencies import (
    get_analysis_chain, get_cache, get_processing_pipeline,
    get_raw_store, get_vector_store,
)
from review_intel.collectors.registry import collect_from_all
from review_intel.domain.waba_classifier import WABAClassifier
from review_intel.schemas.review import Platform, ReviewSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2", tags=["review-intelligence"])


class ScrapeRequest(BaseModel):
    companies: list[str]
    platforms: list[str] | None = None
    max_reviews_per_source: int = 100


@router.post("/scrape")
async def scrape_reviews(request: ScrapeRequest):
    store = get_vector_store()
    raw_store = get_raw_store()
    pipeline = get_processing_pipeline()
    platform_map = {p.value: p for p in Platform}
    results = []

    for company in request.companies:
        try:
            platforms = [platform_map[p] for p in (request.platforms or []) if p in platform_map] or None
            raw = await collect_from_all(company, request.max_reviews_per_source, platforms)
            await raw_store.save_reviews(raw)
            processed = await pipeline.process(raw)
            if processed.output:
                store.index_reviews(processed.output, company)
            sources = {}
            for r in processed.output:
                sources[r.platform.value] = sources.get(r.platform.value, 0) + 1
            results.append({"company": company, "collected": len(raw),
                           "processed": len(processed.output), "sources": sources, "status": "success"})
        except Exception as e:
            logger.exception("Scrape failed for %s", company)
            results.append({"company": company, "collected": 0, "processed": 0, "sources": {}, "status": f"error: {e}"})
    return {"results": results}


@router.post("/analyze/{company}")
async def analyze_company(company: str):
    raw_store = get_raw_store()
    chain = get_analysis_chain()
    cache = get_cache()

    cached = cache.get(f"analysis:{company}")
    if cached:
        return cached

    reviews = await raw_store.get_reviews(company, limit=5000)
    if not reviews:
        store = get_vector_store()
        texts = store.get_all_reviews(company)
        if not texts:
            raise HTTPException(404, f"No reviews for {company}")
        reviews = [ReviewSchema(text=t, competitor_name=company) for t in texts if len(t) > 15]

    if not chain:
        raise HTTPException(503, "No LLM configured")

    result = await chain.analyze(reviews, company)
    classifier = WABAClassifier()
    classifications = classifier.classify_batch(reviews)
    result.pipeline_metadata["waba_themes"] = {
        k.value: v for k, v in classifier.get_theme_distribution(classifications).items()
    }
    response = result.model_dump()
    cache.set(f"analysis:{company}", response)
    return response


@router.get("/status/{company}")
async def company_status(company: str):
    raw_store = get_raw_store()
    store = get_vector_store()
    return {"company": company, "raw": await raw_store.count(company), "indexed": store.count(company)}


@router.get("/companies")
async def list_companies():
    raw_store = get_raw_store()
    companies = await raw_store.get_companies()
    return {"companies": [{"name": c, "count": await raw_store.count(c)} for c in companies]}


@router.delete("/clear/{company}")
async def clear_company(company: str):
    deleted = await get_raw_store().delete_company(company)
    get_vector_store().clear_company(company)
    get_cache().invalidate(f"analysis:{company}")
    return {"status": "cleared", "company": company, "deleted": deleted}


@router.get("/search")
async def semantic_search(query: str, company: str | None = None, n: int = 20):
    results = get_vector_store().search(query, company=company, n_results=n)
    return {"query": query, "results": results, "count": len(results)}
