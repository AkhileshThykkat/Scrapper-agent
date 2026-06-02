"""
Redesigned Gradio UI for the Review Intelligence Platform.

Replaces the original ui.py with tabs for multi-company scraping,
WABA-aware analysis, competitor intelligence, and semantic search.
"""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from datetime import datetime

import gradio as gr

from review_intel.api.dependencies import (
    get_analysis_chain, get_processing_pipeline,
    get_raw_store, get_vector_store,
)
from review_intel.collectors.registry import collect_from_all
from review_intel.config import get_settings
from review_intel.domain.waba_classifier import WABAClassifier
from review_intel.schemas.review import Platform

logger = logging.getLogger(__name__)

CSS = """
.gradio-container { max-width: 100% !important; }
footer { display: none !important; }
.stat-box { text-align: center; padding: 12px; border-radius: 8px; }
"""


async def _run_scrape(companies_text: str, max_reviews: int, progress=gr.Progress()):
    companies = [c.strip() for c in companies_text.split(",") if c.strip()]
    if not companies:
        return "Enter at least one company name."

    store = get_vector_store()
    raw_store = get_raw_store()
    pipeline = get_processing_pipeline()
    results = []

    for i, company in enumerate(companies):
        progress((i) / len(companies), desc=f"Collecting reviews for {company}...")
        try:
            raw = await collect_from_all(company, max_reviews_per_source=max_reviews)
            await raw_store.save_reviews(raw)

            progress((i + 0.5) / len(companies), desc=f"Processing {company}...")
            processed = await pipeline.process(raw)
            if processed.output:
                store.index_reviews(processed.output, company)

            sources = {}
            for r in processed.output:
                sources[r.platform.value] = sources.get(r.platform.value, 0) + 1

            results.append(
                f"**{company}**: {len(raw)} collected → {len(processed.output)} after processing "
                f"({', '.join(f'{v} from {k}' for k, v in sources.items())})"
            )
        except Exception as e:
            logger.exception("Scrape failed for %s", company)
            results.append(f"**{company}**: Error — {e}")

    progress(1.0, desc="Done!")
    return "\n\n".join(results)


async def _run_analysis(company: str, progress=gr.Progress()):
    if not company:
        return "Select a company first.", ""

    progress(0, desc=f"Loading reviews for {company}...")
    raw_store = get_raw_store()
    reviews = await raw_store.get_reviews(company, limit=5000)

    if not reviews:
        store = get_vector_store()
        texts = store.get_all_reviews(company)
        if not texts:
            return f"No reviews found for **{company}**. Scrape first.", ""
        from review_intel.schemas.review import ReviewSchema
        reviews = [ReviewSchema(text=t, competitor_name=company) for t in texts if len(t) > 15]

    chain = get_analysis_chain()
    if not chain:
        return "No LLM configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_BASE_URL.", ""

    progress(0.2, desc="Running analysis chain...")
    result = await chain.analyze(reviews, company)

    # WABA classification
    progress(0.8, desc="Classifying WABA themes...")
    classifier = WABAClassifier()
    classifications = classifier.classify_batch(reviews)
    theme_dist = classifier.get_theme_distribution(classifications)

    # Build markdown report
    report = f"# Analysis: {company}\n\n"
    report += f"**Reviews analyzed:** {result.review_count} | "
    report += f"**Overall sentiment:** {result.overall_sentiment:.2f} | "
    report += f"**Method:** {result.analysis_method}\n\n"

    if result.executive_summary:
        report += f"## Executive Summary\n\n{result.executive_summary}\n\n"

    if result.pain_points:
        report += "## Pain Points\n\n"
        for pp in sorted(result.pain_points, key=lambda p: p.severity, reverse=True):
            report += f"- **{pp.description}** (severity: {pp.severity}, freq: {pp.frequency}, confidence: {pp.confidence_score})\n"
        report += "\n"

    if result.feature_requests:
        report += "## Feature Requests\n\n"
        for fr in result.feature_requests:
            report += f"- **{fr.description}** (urgency: {fr.urgency}, freq: {fr.frequency})\n"
        report += "\n"

    if result.themes:
        report += "## Theme Analysis\n\n"
        for t in result.themes:
            emoji = "🟢" if t.sentiment_score > 0.2 else "🔴" if t.sentiment_score < -0.2 else "🟡"
            report += f"- {emoji} **{t.theme}** — sentiment: {t.sentiment_score:.2f}, freq: {t.frequency}\n"
        report += "\n"

    if theme_dist:
        report += "## WABA Theme Distribution\n\n"
        for theme, count in list(theme_dist.items())[:15]:
            report += f"- **{theme.value}**: {count} reviews\n"
        report += "\n"

    progress(1.0, desc="Analysis complete!")
    return report, result.model_dump_json(indent=2)


async def _semantic_search(query: str, company: str | None):
    if not query:
        return "Enter a search query."
    store = get_vector_store()
    results = store.search(query, company=company or None, n_results=15)
    if not results:
        return "No results found."
    output = f"### {len(results)} results for: *{query}*\n\n"
    for i, r in enumerate(results, 1):
        meta = r.get("metadata", {})
        platform = meta.get("platform", "?")
        rating = meta.get("rating", "")
        output += f"**{i}.** [{platform}] {f'⭐{rating}' if rating else ''}\n> {r['text'][:300]}\n\n"
    return output


async def _get_stats():
    raw_store = get_raw_store()
    companies = await raw_store.get_companies()
    if not companies:
        return [["No data", "0"]]
    rows = []
    for c in companies:
        count = await raw_store.count(c)
        rows.append([c, str(count)])
    return rows


def create_gradio_app():
    settings = get_settings()

    with gr.Blocks(title="Review Intelligence Platform", css=CSS) as app:
        gr.Markdown("# 🔍 Review Intelligence Platform\n*WABA & SaaS Customer Intelligence*")

        with gr.Tab("📥 Collect Reviews"):
            companies_input = gr.Textbox(
                label="Company Names", placeholder="Interakt, Wati, AiSensy, Gallabox",
                info="Comma-separated. Uses G2, Capterra, Trustpilot, and Google.",
            )
            max_reviews = gr.Number(label="Max reviews per source", value=100, minimum=10, maximum=500)
            scrape_btn = gr.Button("Start Collection", variant="primary", size="lg")
            scrape_output = gr.Markdown(label="Results")
            scrape_btn.click(fn=_run_scrape, inputs=[companies_input, max_reviews], outputs=scrape_output)

        with gr.Tab("📊 Analyze"):
            analysis_company = gr.Textbox(label="Company", placeholder="Exact company name")
            analyze_btn = gr.Button("Run Analysis Chain", variant="primary", size="lg")
            analysis_report = gr.Markdown(label="Report")
            analysis_json = gr.Code(label="Raw JSON", language="json", visible=False)
            show_json = gr.Checkbox(label="Show raw JSON")
            show_json.change(fn=lambda v: gr.update(visible=v), inputs=show_json, outputs=analysis_json)
            analyze_btn.click(fn=_run_analysis, inputs=[analysis_company], outputs=[analysis_report, analysis_json])

        with gr.Tab("🔎 Search"):
            search_query = gr.Textbox(label="Query", placeholder="template approval issues")
            search_company = gr.Textbox(label="Company (optional)", placeholder="Filter by company")
            search_btn = gr.Button("Search", variant="primary")
            search_output = gr.Markdown()
            search_btn.click(fn=_semantic_search, inputs=[search_query, search_company], outputs=search_output)

        with gr.Tab("📈 Dashboard"):
            gr.Markdown("### Indexed Companies")
            stats_table = gr.Dataframe(headers=["Company", "Reviews"])
            refresh_btn = gr.Button("Refresh", size="sm")
            refresh_btn.click(fn=_get_stats, outputs=stats_table)

            gr.Markdown(f"### Configuration\n- **LLM:** {settings.active_llm_description}\n"
                       f"- **Vector Store:** {settings.vector_store_backend.value}")

    return app
