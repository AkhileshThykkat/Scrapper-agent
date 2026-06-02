"""
Redesigned Gradio UI — renders thorough, evidence-rich analysis reports.
"""

from __future__ import annotations

import asyncio
import json
import logging

import gradio as gr

from review_intel.api.dependencies import (
    get_analysis_chain, get_processing_pipeline,
    get_raw_store, get_vector_store,
)
from review_intel.collectors.registry import collect_from_all
from review_intel.config import get_settings
from review_intel.delivery.pdf_generator import generate_report_pdf
from review_intel.domain.waba_classifier import WABAClassifier

logger = logging.getLogger(__name__)

CSS = """
.gradio-container { max-width: 100% !important; }
footer { display: none !important; }
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
        progress(i / len(companies), desc=f"Collecting reviews for {company}...")
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
                f"### ✅ {company}\n"
                f"- **Collected:** {len(raw)} reviews\n"
                f"- **After processing:** {len(processed.output)} reviews "
                f"({len(raw) - len(processed.output)} removed by dedup/spam/quality filters)\n"
                f"- **Sources:** {', '.join(f'{v} from {k}' for k, v in sources.items())}\n"
            )
        except Exception as e:
            results.append(f"### ❌ {company}\nError: {e}\n")

    progress(1.0, desc="Done!")
    return "\n".join(results)


def _render_report(result) -> str:
    """Render an AnalysisResult dict into a thorough markdown report."""
    r = result
    date_val = r.get('analysis_date')
    if hasattr(date_val, 'strftime'):
        date_str = date_val.strftime("%Y-%m-%d")
    elif isinstance(date_val, str):
        date_str = date_val[:10]
    else:
        date_str = "N/A"
        
    report = f"# 📊 Review Intelligence Report: {r['company']}\n\n"
    report += f"**Date:** {date_str} | "
    report += f"**Reviews:** {r['review_count']} | "
    report += f"**Sentiment:** {r['overall_sentiment']:.2f} | "
    report += f"**Method:** {r.get('analysis_method', 'N/A')}\n\n"

    # Source breakdown
    if r.get("source_breakdown"):
        report += "**Sources:** " + ", ".join(f"{v} from {k}" for k, v in r["source_breakdown"].items()) + "\n\n"

    report += "---\n\n"

    # Executive Summary (the richest section)
    if r.get("executive_summary"):
        report += r["executive_summary"] + "\n\n---\n\n"

    # Pain Points — thorough rendering
    if r.get("pain_points"):
        report += "## 🔴 Pain Points\n\n"
        for i, pp in enumerate(r["pain_points"], 1):
            severity = pp.get("severity", 0)
            emoji = "🔴" if severity >= 70 else "🟠" if severity >= 40 else "🟡"
            report += f"### {emoji} {i}. {pp.get('description', 'Unknown')}\n\n"
            report += f"**Severity:** {severity}/100 | **Frequency:** {pp.get('frequency', '?')} reviews | "
            report += f"**Category:** {pp.get('category', '?')} | **Confidence:** {pp.get('confidence_score', '?')}%\n\n"

            if pp.get("root_cause_analysis"):
                report += f"**Root Cause:** {pp['root_cause_analysis']}\n\n"
            if pp.get("user_impact"):
                report += f"**User Impact:** {pp['user_impact']}\n\n"
            if pp.get("affected_segments"):
                report += f"**Affected Segments:** {pp['affected_segments']}\n\n"

            quotes = pp.get("evidence_quotes", [])
            if quotes:
                report += "**Customer Evidence:**\n"
                for q in quotes[:4]:
                    report += f'> *"{q}"*\n\n'

            if pp.get("business_impact"):
                report += f"**Business Impact:** {pp['business_impact']}\n\n"
            if pp.get("recommended_fix"):
                report += f"**💡 Recommended Fix:** {pp['recommended_fix']}\n\n"
            report += "---\n\n"

    # Feature Requests — thorough rendering
    if r.get("feature_requests"):
        report += "## 💡 Feature Requests\n\n"
        for i, fr in enumerate(r["feature_requests"], 1):
            urgency = fr.get("urgency", "medium")
            emoji = "🔴" if urgency == "critical" else "🟠" if urgency == "high" else "🟡" if urgency == "medium" else "⚪"
            report += f"### {emoji} {i}. {fr.get('description', 'Unknown')}\n\n"
            report += f"**Urgency:** {urgency} | **Frequency:** {fr.get('frequency', '?')} | "
            report += f"**Confidence:** {fr.get('confidence_score', '?')}%\n\n"

            if fr.get("use_case"):
                report += f"**Why users want this:** {fr['use_case']}\n\n"
            if fr.get("current_workaround"):
                report += f"**Current workaround:** {fr['current_workaround']}\n\n"
            if fr.get("competitive_context"):
                report += f"**Competitive context:** {fr['competitive_context']}\n\n"

            quotes = fr.get("evidence_quotes", [])
            if quotes:
                report += "**Customer Voices:**\n"
                for q in quotes[:3]:
                    report += f'> *"{q}"*\n\n'

            if fr.get("prioritization_rationale"):
                report += f"**Prioritization rationale:** {fr['prioritization_rationale']}\n\n"
            report += "---\n\n"

    # Theme Analysis — thorough rendering
    if r.get("themes"):
        report += "## 🏷️ Theme Analysis\n\n"
        for t in r["themes"]:
            sentiment = t.get("sentiment_score", 0)
            emoji = "🟢" if sentiment > 0.2 else "🔴" if sentiment < -0.2 else "🟡"
            report += f"### {emoji} {t.get('theme', 'Unknown')}\n\n"
            report += f"**Sentiment:** {sentiment:.2f} | **Frequency:** {t.get('frequency', '?')} | "
            report += f"**Severity:** {t.get('severity_score', '?')}/100 | **Trend:** {t.get('trend_direction', '?')}\n\n"

            if t.get("analysis"):
                report += f"{t['analysis']}\n\n"

            quotes = t.get("key_quotes", [])
            if quotes:
                report += "**Key Quotes:**\n"
                for q in quotes[:3]:
                    report += f'> *"{q}"*\n\n'

            recs = t.get("recommendations", [])
            if recs:
                report += "**Recommendations:**\n"
                for rec in recs:
                    report += f"- {rec}\n"
                report += "\n"
            report += "---\n\n"

    # Competitive Intelligence
    ci = r.get("pipeline_metadata", {}).get("competitive_intel") or {}
    if not ci and r.get("insights"):
        # Check if competitive data is in the pipeline_metadata
        pass

    # WABA Theme Distribution
    waba = r.get("pipeline_metadata", {}).get("waba_themes", {})
    if waba:
        report += "## 📱 WABA Theme Distribution\n\n"
        for theme, count in sorted(waba.items(), key=lambda x: x[1], reverse=True)[:12]:
            bar = "█" * min(count, 20)
            report += f"- **{theme}**: {count} reviews {bar}\n"
        report += "\n"

    return report


async def _run_analysis(company: str, progress=gr.Progress()):
    if not company:
        return "Select a company first.", "", gr.update(visible=False)

    progress(0, desc=f"Loading reviews for {company}...")
    raw_store = get_raw_store()
    reviews = await raw_store.get_reviews(company, limit=5000)

    if not reviews:
        store = get_vector_store()
        texts = store.get_all_reviews(company)
        if not texts:
            return f"No reviews found for **{company}**. Scrape first.", "", gr.update(visible=False)
        from review_intel.schemas.review import ReviewSchema
        reviews = [ReviewSchema(text=t, competitor_name=company) for t in texts if len(t) > 15]

    chain = get_analysis_chain()
    if not chain:
        return "No LLM configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or OLLAMA_BASE_URL in your `.env` file.", "", gr.update(visible=False)

    progress(0.1, desc="Step 1/6: Extracting structured facts with evidence...")
    result = await chain.analyze(reviews, company)

    progress(0.9, desc="Classifying WABA themes...")
    classifier = WABAClassifier()
    classifications = classifier.classify_batch(reviews)
    result.pipeline_metadata["waba_themes"] = {
        k.value: v for k, v in classifier.get_theme_distribution(classifications).items()
    }

    result_dict = result.model_dump()
    report = _render_report(result_dict)

    # Generate PDF report
    progress(0.95, desc="Generating PDF report...")
    try:
        pdf_path = generate_report_pdf(result_dict)
        pdf_update = gr.update(value=pdf_path, visible=True)
    except Exception as e:
        logger.exception("Failed to generate PDF")
        pdf_update = gr.update(visible=False)

    progress(1.0, desc="Analysis complete!")
    return report, json.dumps(result_dict, indent=2, default=str), pdf_update


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
        reviewer = meta.get("reviewer", "")
        role = meta.get("reviewer_role", "")
        reviewer_info = f" — *{reviewer}*" if reviewer else ""
        role_info = f" ({role})" if role else ""
        output += f"**{i}.** [{platform}] {f'⭐{rating} ' if rating else ''}{reviewer_info}{role_info}\n"
        output += f"> {r['text'][:400]}\n\n"
    return output


async def _get_stats():
    raw_store = get_raw_store()
    companies = await raw_store.get_companies()
    if not companies:
        return [["No data yet", "—"]]
    rows = []
    for c in companies:
        count = await raw_store.count(c)
        rows.append([c, str(count)])
    return rows


def create_gradio_app():
    settings = get_settings()

    with gr.Blocks(title="Review Intelligence Platform", css=CSS) as app:
        gr.Markdown(
            "# 🔍 Review Intelligence Platform\n"
            "*Evidence-backed WABA & SaaS customer intelligence*"
        )

        with gr.Tab("📥 Collect Reviews"):
            companies_input = gr.Textbox(
                label="Company Names",
                placeholder="Interakt, Wati, AiSensy, Gallabox, DoubleTick",
                info="Comma-separated. Collects from G2, Capterra, Trustpilot, and Google.",
            )
            max_reviews = gr.Number(label="Max reviews per source", value=100, minimum=10, maximum=500)
            scrape_btn = gr.Button("🚀 Start Collection", variant="primary", size="lg")
            scrape_output = gr.Markdown(label="Results")
            scrape_btn.click(fn=_run_scrape, inputs=[companies_input, max_reviews], outputs=scrape_output)

        with gr.Tab("📊 Analyze"):
            gr.Markdown(
                "Run the **6-step analysis chain**: extraction → themes → pain points "
                "→ feature requests → competitive intel → executive summary"
            )
            analysis_company = gr.Textbox(label="Company", placeholder="Exact company name")
            analyze_btn = gr.Button("🧠 Run Full Analysis", variant="primary", size="lg")
            pdf_download = gr.File(label="📄 Download PDF Report", visible=False)
            analysis_report = gr.Markdown(label="Report")
            analysis_json = gr.Code(label="Raw JSON", language="json", visible=False)
            show_json = gr.Checkbox(label="Show raw JSON output")
            show_json.change(fn=lambda v: gr.update(visible=v), inputs=show_json, outputs=analysis_json)
            analyze_btn.click(
                fn=_run_analysis,
                inputs=[analysis_company],
                outputs=[analysis_report, analysis_json, pdf_download]
            )

        with gr.Tab("🔎 Semantic Search"):
            search_query = gr.Textbox(label="Query", placeholder="e.g. template approval problems")
            search_company = gr.Textbox(label="Company filter (optional)")
            search_btn = gr.Button("Search", variant="primary")
            search_output = gr.Markdown()
            search_btn.click(fn=_semantic_search, inputs=[search_query, search_company], outputs=search_output)

        with gr.Tab("📈 Dashboard"):
            gr.Markdown("### Indexed Companies")
            stats_table = gr.Dataframe(headers=["Company", "Reviews"])
            refresh_btn = gr.Button("🔄 Refresh", size="sm")
            refresh_btn.click(fn=_get_stats, outputs=stats_table)
            gr.Markdown(
                f"### Configuration\n"
                f"- **LLM:** {settings.active_llm_description}\n"
                f"- **Vector Store:** {settings.vector_store_backend.value}\n"
                f"- **Analysis Steps:** 6 (extraction → themes → pain points → features → competitive → summary)"
            )

    return app
