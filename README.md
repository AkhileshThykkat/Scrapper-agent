# Review Scraper & Analyzer Agent

An AI-powered agent designed to scrape and analyze customer reviews for any company. It autonomously navigates the web (using human-like browsing patterns) to collect reviews from Google Search, Trustpilot, G2, Capterra, Reddit, and other sources. 

Once scraped, reviews are indexed into a local vector database (ChromaDB) and analyzed by an LLM to automatically categorize pain points (Technical, UI/UX, Support), extract positive themes, and determine overall sentiment.

## Features

- 🕵️ **Human-like Scraping**: Uses Playwright with anti-detection features (randomized user agents, organic scrolling/clicking) to minimize blocks.
- 🔍 **Semantic Search**: Embeds reviews using `sentence-transformers` and stores them in a local ChromaDB instance.
- 🧠 **LLM Analysis**: Analyzes pain points and sentiment using local models (via Ollama) or cloud providers (OpenAI, Anthropic).
- 📊 **Interactive Dashboard**: Clean Gradio web UI to trigger scrapes and view interactive HTML reports.
- 📄 **PDF Export**: Generates and downloads a structured PDF report of the analysis for offline sharing.

## Requirements

- Python 3.12+
- `uv` (recommended for dependency management)
- [Ollama](https://ollama.com/) (Optional: if running local open-source LLMs)

## Installation

1. **Install dependencies**:
   This project uses `uv` for package management. From the project root, run:
   ```bash
   uv sync
   ```

2. **Install Playwright Browsers**:
   The scraper relies on headless Chromium. Install it via Playwright:
   ```bash
   uv run playwright install chromium
   ```

## Configuration

The project requires an LLM to perform deep analysis (though it has a keyword-based fallback if none is provided). 

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` to configure your preferred LLM:

**Option 1: Local LLM (Default)**
```env
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_MODEL=gemma:2b  # or llama3, mistral, etc.
```

**Option 2: Cloud APIs**
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
# OR
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
```

## Usage

Start the application:

```bash
uv run main.py
```

The FastAPI server will start, and your default browser should automatically open the UI at:
**`http://127.0.0.1:8000/gradio`**

### Recommended Workflow

1. **Scrape**: Go to the **Scrape Reviews** tab. Enter a company name (e.g., "Stripe"). You can specify the number of reviews you want to target (e.g., 200). Click **Start Scraping**. The agent will search Google and review sites.
2. **Analyze**: Navigate to the **Analyze Reviews** tab. Enter the exact company name you just scraped and click **Generate Analysis Report**. The agent will chunk the reviews, pass them to your configured LLM, and synthesize an executive summary.
3. **Export**: The dashboard will display the main pain points categorized by technical, UI, and support. A PDF version will also be available for download.

## Architecture

- `main.py` - FastAPI entry point; mounts the API and Gradio UI.
- `agent/scraper.py` - Search footprint logic and extraction heuristics.
- `agent/browser.py` - The `HumanBrowser` wrapper extending Playwright.
- `agent/embeddings.py` - Local ChromaDB management.
- `agent/analyzer.py` - Prompt construction and multi-LLM routing.
- `agent/ui.py` - Gradio dashboard structure.
- `agent/dashboard.py` & `agent/report.py` - HTML and PDF report builders.
