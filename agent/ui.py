import asyncio
import logging
import os
import tempfile
from datetime import datetime

import gradio as gr

from agent.report import generate_report_pdf
from agent.scraper import scrape_reviews
from agent.embeddings import ReviewVectorStore
from agent.analyzer import analyze_reviews, search_based_analysis, _detect_method
from agent.dashboard import render_dashboard

logger = logging.getLogger(__name__)

store = ReviewVectorStore()


async def run_scrape(companies_text: str, extra_sites_text: str, num_reviews: int, progress=gr.Progress()):
    companies = [c.strip() for c in companies_text.split(",") if c.strip()]
    extra_sites = [s.strip() for s in extra_sites_text.split("\n") if s.strip()] if extra_sites_text else None

    if not companies:
        return "Please enter at least one company name."

    progress(0, desc="Initializing browser...")
    results = []
    total = len(companies)

    for i, company in enumerate(companies):
        progress((i) / total, desc=f"Scraping {num_reviews} reviews for {company}...")
        try:
            store.clear_company(company)
            timeout_budget = max(300, num_reviews * 3)
            reviews = await asyncio.wait_for(
                scrape_reviews(company, extra_sites, max_reviews=num_reviews),
                timeout=timeout_budget,
            )
            if reviews:
                store.index_reviews(reviews, company)
            results.append(f"{company}: {len(reviews)} unique reviews scraped and indexed")
        except asyncio.TimeoutError:
            results.append(f"{company}: Timed out after {timeout_budget} seconds")
        except Exception as e:
            logger.exception(f"Failed for {company}")
            results.append(f"{company}: Error - {str(e)}")

    progress(1.0, desc="Done!")
    return "\n".join(results)


async def run_analysis(company: str, use_semantic: bool = False, progress=gr.Progress()):
    if not company:
        return "Please select a company first.", None

    progress(0, desc=f"Analyzing reviews for {company}...")
    reviews = store.get_all_reviews(company)
    if not reviews:
        return f"No reviews found for {company}. Please scrape first.", None

    def analyze():
        if use_semantic:
            return search_based_analysis(store, company)
        return analyze_reviews(reviews, company, store)

    loop = asyncio.get_event_loop()
    report = await loop.run_in_executor(None, analyze)
    progress(0.8, desc="Generating PDF...")

    method = _detect_method()
    dashboard_html = render_dashboard(report, company, len(reviews), method)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_bytes = generate_report_pdf(company, report, len(reviews), timestamp)

    safe_name = company.replace(" ", "_").replace("/", "_")
    pdf_path = os.path.join(tempfile.gettempdir(), f"review_report_{safe_name}_{timestamp}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    progress(1.0, desc="Analysis complete!")
    return dashboard_html, pdf_path


def get_companies():
    try:
        all_data = store.collection.get()
        companies = set()
        if all_data and all_data.get("metadatas"):
            for meta in all_data["metadatas"]:
                if meta and "company" in meta:
                    companies.add(meta["company"])
        return list(companies)
    except Exception:
        return []


def get_stats():
    try:
        all_data = store.collection.get()
        counts = {}
        if all_data and all_data.get("metadatas"):
            for meta in all_data["metadatas"]:
                if meta and "company" in meta:
                    c = meta["company"]
                    counts[c] = counts.get(c, 0) + 1
        if not counts:
            return [["No data", "0"]]
        return [[c, str(n)] for c, n in sorted(counts.items())]
    except Exception:
        return [["Error loading stats", ""]]


def _format_companies(companies):
    if not companies:
        return "No companies scraped yet. Go to the Scrape tab first."
    return "Indexed companies: " + ", ".join(f"**{c}**" for c in sorted(companies))


CSS = """
.gradio-container { max-width: 100% !important; }
.tab-nav { font-size: 14px; }
footer { display: none !important; }
"""


def create_gradio_app():
    with gr.Blocks(title="Review Scraper & Analyzer Agent", css=CSS) as app:
        gr.Markdown("# Review Scraper & Analyzer Agent", elem_classes="compact-header")

        with gr.Tab("Scrape Reviews"):
            companies_input = gr.Textbox(
                label="Company Names",
                placeholder="e.g., Apple, Microsoft, Tesla",
                info="Separate multiple names with commas",
            )
            with gr.Row():
                num_reviews_input = gr.Number(
                    label="Number of reviews to scrape",
                    value=200,
                    minimum=10,
                    maximum=500,
                    step=10,
                    precision=0,
                )
                extra_sites_input = gr.Textbox(
                    label="Additional Review Sites",
                    placeholder="https://www.trustpilot.com/review/companyname",
                    lines=2,
                    info="One URL per line (Google Reviews always included)",
                    scale=2,
                )
            scrape_btn = gr.Button("Start Scraping (clears old data for fresh scrape)", variant="primary", size="lg")
            scrape_output = gr.Textbox(label="Results", lines=5)

        with gr.Tab("Analyze Reviews"):
            analysis_company = gr.Textbox(
                label="Company Name",
                placeholder="Type the exact company name you scraped",
            )
            use_semantic = gr.Checkbox(
                label="Use semantic search analysis",
                info="Vector search for pain points & positives",
            )
            analyze_btn = gr.Button("Generate Analysis Report", variant="primary", size="lg")
            analysis_output = gr.HTML(label="Report")
            pdf_download = gr.File(label="Download PDF", visible=True)

            analyze_btn.click(
                fn=run_analysis,
                inputs=[analysis_company, use_semantic],
                outputs=[analysis_output, pdf_download],
            )

            gr.Markdown("---")
            available_companies = gr.Markdown("No companies scraped yet.")
            gr.Button("Refresh Companies", size="sm", variant="secondary").click(
                fn=lambda: _format_companies(get_companies()),
                outputs=available_companies,
            )
            stats_output = gr.Dataframe(
                label="Review Counts",
                headers=["Company", "Reviews"],
            )
            gr.Button("Refresh Stats", size="sm").click(fn=get_stats, outputs=stats_output)

        with gr.Tab("Configuration"):
            gr.Markdown(
                """
                | Variable | Description |
                |---|---|
                | `OLLAMA_BASE_URL` | Local LLM via Ollama (e.g. `http://localhost:11434`) |
                | `LOCAL_MODEL` | Model name (default: `gemma3:12b`) |
                | `OPENAI_API_KEY` | OpenAI key for cloud AI analysis |
                | `ANTHROPIC_API_KEY` | Anthropic key for cloud AI analysis |

                If no LLM is configured, the agent falls back to keyword-based analysis.
                """
            )

        scrape_btn.click(
            fn=run_scrape,
            inputs=[companies_input, extra_sites_input, num_reviews_input],
            outputs=scrape_output,
        ).then(
            fn=lambda c: c.split(",")[0].strip() if c else "",
            inputs=companies_input,
            outputs=analysis_company,
        )

    return app
