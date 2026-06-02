# Scrapper-Agent Architecture Audit

**Audit Date:** 2026-06-02  
**Auditor:** Principal AI Engineer  
**Scope:** Complete repository — all 8 source files, 1,706 lines of application code  
**Branch Audited:** `prod` (HEAD: `a66eb0c`)

---

## Executive Summary

The current codebase is a **working prototype** — it can scrape text from Google search results, store embeddings in ChromaDB, run a basic LLM-powered or keyword-based analysis, and render results as an HTML dashboard or PDF. However, it has **zero production readiness** for the stated goal of becoming a customer intelligence platform for WABA/SaaS ecosystems.

**Critical gaps:** No structured data extraction, no review metadata, no multi-step analysis, no confidence scoring, no evidence linking, no competitor intelligence, no domain-specific models, no tests, no async pipeline, no retry/rate-limit handling, and significant hallucination risk from single-pass LLM prompting.

**Severity Distribution:**
- 🔴 Critical (blocks production use): 14 findings
- 🟠 Major (degrades quality significantly): 11 findings
- 🟡 Minor (tech debt): 8 findings

---

## 1. Poor Abstractions

### 🔴 1.1 God Module: `scraper.py` (508 lines)

The scraper module conflates:
- URL construction logic
- Browser navigation
- DOM extraction (JavaScript evaluation)
- Noise filtering heuristics
- Review-like text detection
- Site-specific selector management
- Pagination handling
- CAPTCHA detection

All of these concerns live in a single flat file with no class hierarchy, no strategy pattern for different sites, and no separation between "page navigation" and "data extraction."

**Impact:** Cannot add a new review source without modifying the monolith. Cannot test extraction logic independently from browser automation.

### 🔴 1.2 God Module: `analyzer.py` (317 lines)

The analyzer module conflates:
- LLM provider detection and routing (`_detect_method`, `_call_llm`)
- Keyword-based fallback analysis (`_fallback_analysis`)
- Chunk-based LLM analysis with synthesis (`analyze_reviews`)
- Semantic-search-based analysis (`search_based_analysis`)
- Evidence extraction (`_extract_evidence`)
- Report formatting (`_build_evidence_section`, `_add_header`)

**Impact:** Cannot swap analysis strategies. Cannot test LLM prompting independently. Cannot add new analysis dimensions without touching the entire file.

### 🟠 1.3 No Interface/Protocol Abstractions

There are zero abstract base classes, protocols, or interfaces. The `HumanBrowser` class is reasonable but is the *only* class with a clean contract (`__aenter__`/`__aexit__`). Everything else is procedural functions with implicit coupling.

### 🟡 1.4 Hardcoded Review Schema

Reviews are represented as `dict` with keys `{"text", "source"}` — no Pydantic model, no validation, no type safety. The embeddings module adds `rating`, `reviewer`, `date` to metadata but they're *never populated by the scraper*.

---

## 2. Tight Coupling

### 🔴 2.1 Global Singleton Vector Store

Both `routes.py` and `ui.py` instantiate `ReviewVectorStore()` at module level:
```python
# routes.py line 14
store = ReviewVectorStore()

# ui.py line 17
store = ReviewVectorStore()
```
These are **two separate ChromaDB clients** pointing at the same `./chroma_data` directory. This creates race conditions and makes dependency injection impossible.

### 🟠 2.2 LLM Client Creation Inside Business Logic

`_call_llm()` creates a new `OpenAI()` or `anthropic.Anthropic()` client on *every call*. No connection pooling, no client reuse, no dependency injection. The imports are *inside* the function body (lazy imports), which masks dependency errors until runtime.

### 🟠 2.3 Scraper ↔ Browser Coupling

The `scrape_reviews()` function creates and manages the browser lifecycle internally. The caller cannot provide a pre-configured browser, share a browser across companies, or inject a mock browser for testing.

---

## 3. Review-Processing Bottlenecks

### 🔴 3.1 Sequential Company Scraping

`scrape_reviews()` processes one company at a time. When scraping multiple companies via the UI, each company waits for the previous one to finish. With 15 WABA competitors, this means 15 × (120–300s) = **30–75 minutes** of sequential waiting.

### 🔴 3.2 No Async Pipeline

The analysis pipeline is blocking:
1. `analyze_reviews()` calls `_call_llm()` synchronously
2. The Gradio UI wraps it in `run_in_executor()` but this just moves blocking to a thread pool
3. ChromaDB operations are synchronous
4. PDF generation is synchronous

For 10,000+ reviews chunked at 40 per batch, the LLM alone requires `250 × 3-5s = 750-1250s` of sequential API calls.

### 🟠 3.3 Fixed Chunk Size (40 Reviews)

The chunk size is hardcoded at 40. No consideration for token limits, model context windows, or optimal batch sizes. A chunk of 40 long reviews could exceed context limits; a chunk of 40 short reviews wastes context.

---

## 4. Hallucination Risks

### 🔴 4.1 Two-Step Analysis is Still Too Shallow

The current pipeline:
1. Chunk reviews → ask LLM for pain points + positives (per chunk)
2. Synthesize chunks → ask LLM for combined report

This is a **single conceptual pass** with a merge step. The synthesis prompt says "combine these analyses" but doesn't verify claims, doesn't cross-reference, doesn't score confidence.

### 🔴 4.2 No Structured Output Enforcement

All LLM responses are free-text markdown. The system *hopes* the LLM follows the requested format but has zero validation:
- No JSON schema
- No Pydantic parsing
- No retry on malformed output
- No fallback on partial output

The dashboard parser (`_parse_sections`) uses fragile regex/string matching on LLM output — it will silently drop data if the LLM deviates from the expected heading format.

### 🔴 4.3 No Grounding / Evidence Linking

The evidence section (`_build_evidence_section`) runs *separate* semantic searches after the analysis is done. The evidence is **not linked to specific claims**. The LLM's pain points may not match the evidence at all.

### 🟠 4.4 Prompt Quality

The analysis prompt (line 195-213) asks the LLM to "list exactly what you find" but provides no schema, no examples, and no anti-hallucination guardrails. The synthesis prompt (line 224-249) says "CRITICAL: do not say none mentioned" which is a weak instruction that won't prevent fabrication.

---

## 5. Data-Loss Risks

### 🔴 5.1 Reviews Stored as Text-Only

The scraper extracts raw text but discards:
- Rating (stars)
- Review date
- Reviewer name/role
- Company size
- Verification status
- Review title
- Helpful votes
- Country
- Original URL

The embeddings module has metadata fields for `rating`, `reviewer`, `date` but they default to empty strings because the scraper never extracts them.

### 🟠 5.2 Destructive Re-Scrape

`run_scrape()` in `ui.py` calls `store.clear_company(company)` before scraping. If the scrape fails partway through, all previously indexed reviews are lost.

### 🟡 5.3 No Raw Data Persistence

Scraped reviews go directly into ChromaDB. There is no raw data layer — no JSON dumps, no database tables, no way to replay processing without re-scraping.

---

## 6. Prompt Weaknesses

### 🔴 6.1 No Domain Context

The prompts contain zero WABA/SaaS domain knowledge. The LLM doesn't know what "template approval," "CTWA," "BSP," "embedded signup," or "conversation categories" mean in context. It will misclassify or ignore domain-specific complaints.

### 🟠 6.2 No Few-Shot Examples

The analysis prompt provides zero examples of expected output. Few-shot examples dramatically improve LLM output consistency and quality.

### 🟠 6.3 Generic System Prompt

The system prompt is `"List facts only. No fluff."` or `"You are a professional review analyst."` — these are too generic to produce consistent, high-quality, domain-specific analysis.

---

## 7. Missing Review Metadata

### 🔴 7.1 No Structured Extraction

The scraper extracts `textContent` from DOM nodes. It does not extract:
- Star ratings (available as `aria-label`, `data-rating`, or specific selectors)
- Dates (available as `time` elements or specific selectors)
- Reviewer names
- Pros/cons sections (G2, Capterra have dedicated sections)
- Review titles
- Verification badges

### 🟠 7.2 No Source Differentiation

All reviews are stored with `source: "google_search"` or the raw URL. There's no structured platform identification (G2 vs Capterra vs Trustpilot), no normalization of source metadata.

---

## 8. Scalability Issues

### 🔴 8.1 Single Browser Instance

One browser instance processes all queries sequentially. No browser pooling, no concurrent page loading, no distributed scraping.

### 🟠 8.2 ChromaDB Limitations

ChromaDB is an in-process embedded database. It's suitable for prototyping but:
- No concurrent write safety
- Limited query capabilities
- No built-in backup/restore
- Performance degrades with large collections

### 🟠 8.3 No Caching

Every analysis request re-runs the full LLM pipeline. No caching of:
- Intermediate analysis results
- Embedding computations
- LLM responses

---

## 9. Error Handling Gaps

### 🔴 9.1 Silent Failures in Scraper

Most exceptions in the scraper are caught with broad `except Exception` and logged as warnings. The caller has no way to distinguish between "no reviews exist" and "scraping failed due to CAPTCHA/network/timeout."

### 🟠 9.2 No Retry Logic

Zero retry logic anywhere:
- Failed page loads → skipped
- Failed LLM calls → empty string returned
- Failed DOM extraction → empty list returned
- CAPTCHA → logged and skipped

### 🟡 9.3 No Rate Limiting

No rate limiting on:
- Google search requests (will trigger CAPTCHAs)
- LLM API calls (will hit API rate limits)
- Review site requests (will get blocked)

---

## 10. Cost Inefficiencies

### 🟠 10.1 Redundant LLM Calls

The `search_based_analysis` function searches for pain points AND positives, then sends both to the LLM — but many reviews appear in both result sets due to semantic overlap.

### 🟠 10.2 Large Context Windows Wasted

The chunk prompt includes boilerplate instructions repeated for every chunk. For 250 chunks, this wastes ~250 × 200 tokens = 50,000 tokens on repeated instructions.

### 🟡 10.3 No Cost Tracking

No tracking of API token usage, cost per analysis, or budget enforcement.

---

## 11. Testing & Quality

### 🔴 11.1 Zero Tests

The repository contains zero test files. No unit tests, no integration tests, no benchmarks.

### 🔴 11.2 No CI/CD

No GitHub Actions, no linting, no type checking, no pre-commit hooks.

### 🟡 11.3 Scratch Files in Root

`scratch.py`, `scratch_pdf.py`, `scratch_pdf_test.py`, `scratch_syntax.py`, `scratch_test.py`, `test.pdf`, `test2.pdf` are all development artifacts committed to the repository.

---

## File-by-File Summary

| File | Lines | Role | Issues |
|---|---|---|---|
| `main.py` | 50 | FastAPI app, Gradio mount | Minor — thread-based browser open, no error handling |
| `agent/scraper.py` | 508 | Web scraping | Critical — monolithic, no structured data, no retry |
| `agent/analyzer.py` | 317 | LLM analysis | Critical — no structured output, hallucination risk |
| `agent/browser.py` | 102 | Playwright wrapper | Acceptable — clean async context manager |
| `agent/embeddings.py` | 79 | ChromaDB wrapper | Major — global singleton, sync-only, limited metadata |
| `agent/report.py` | 114 | PDF generation | Minor — ASCII-only, basic formatting |
| `agent/routes.py` | 77 | FastAPI endpoints | Major — duplicate store instance, blocking calls |
| `agent/dashboard.py` | 246 | HTML dashboard | Minor — fragile parsing, hardcoded categories |
| `agent/ui.py` | 213 | Gradio UI | Major — destructive re-scrape, blocking analysis |

---

## Conclusion

The codebase is a **functional prototype** with the right instincts (browser automation, vector search, LLM analysis) but requires a **ground-up redesign** of the data pipeline, analysis architecture, and domain model to become a production-grade customer intelligence platform. The refactor scope is estimated at **~8,000-12,000 lines of new code** across 40-50 files.
