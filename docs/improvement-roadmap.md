# Improvement Roadmap & Migration Plan

**Status:** Pre-Implementation  
**Branch:** `feature/review-intelligence-v2`  
**Estimated Effort:** ~3-4 weeks for a single developer

---

## Branch Strategy

```
main ──────────────────────────────────────────────────────────────→
  │
  └── feature/review-intelligence-v2 ──────────────────────────────→
       │         │         │         │         │         │
       M1        M2        M3        M4        M5        M6
     schemas   collect   process   analysis  intel    delivery
```

### Branch Rules
- All work on `feature/review-intelligence-v2`
- Each milestone = atomic, working state
- Milestone PRs back to `feature/review-intelligence-v2`
- Final PR from `feature/review-intelligence-v2` → `main` after M6

---

## Milestone 1 — Foundation (Days 1-3)

**Objective:** Establish project skeleton, schemas, config, and infrastructure.

### Commits

#### 1.1 Project restructure
- **Rationale:** Move from flat `agent/` to `src/review_intel/` package structure with proper Python packaging
- **Files changed:**
  - `pyproject.toml` — update package name, add `[project.scripts]`, add new dependencies (`pydantic-settings`, `qdrant-client`, `langdetect`, `aiosqlite`)
  - `src/review_intel/__init__.py` — package init
  - `src/review_intel/config.py` — `Settings` class using `pydantic-settings`
- **Impact:** Clean package structure, typed configuration, no runtime behavior change

#### 1.2 Core schemas
- **Rationale:** Define all Pydantic v2 models upfront to establish the data contract
- **Files changed:**
  - `src/review_intel/schemas/review.py` — `ReviewSchema`, `Platform` enum
  - `src/review_intel/schemas/analysis.py` — `PainPoint`, `FeatureRequest`, `ThemeAnalysis`, `ReviewEvidence`, `Insight`, `ReviewCluster`
  - `src/review_intel/schemas/competitor.py` — `CompetitorProfile`, `CompetitorComparison`, `SwitchingPattern`
  - `src/review_intel/schemas/waba.py` — `WABATheme`, `SentimentCategory` enums
- **Impact:** Type-safe data layer, all downstream code has clear contracts

#### 1.3 WABA domain model
- **Rationale:** Encode WhatsApp Business ecosystem knowledge for LLM context and review classification
- **Files changed:**
  - `src/review_intel/domain/waba_taxonomy.py` — concept taxonomy, keyword maps
  - `src/review_intel/domain/platform_registry.py` — target platform metadata (15 WABA competitors)
  - `src/review_intel/domain/ecosystem_context.py` — LLM system prompt context
  - `docs/waba-domain-model.md` — documentation
- **Impact:** Domain knowledge encoded, available for classifiers and LLM prompts

#### 1.4 Store abstraction
- **Rationale:** Abstract storage behind protocols for swappable implementations
- **Files changed:**
  - `src/review_intel/store/base.py` — `VectorStore` and `RawStore` protocols
  - `src/review_intel/store/vector_store.py` — Qdrant implementation (ChromaDB fallback)
  - `src/review_intel/store/raw_store.py` — SQLite raw review persistence
  - `src/review_intel/store/cache.py` — In-memory LRU cache for analysis results
- **Impact:** Raw data preserved, vector search available, no data loss on re-scrape

#### 1.5 Tests foundation
- **Rationale:** Test infrastructure from day one
- **Files changed:**
  - `tests/conftest.py` — fixtures, test settings
  - `tests/unit/test_schemas.py` — schema validation tests
- **Impact:** CI-ready test suite

---

## Milestone 2 — Collection Layer (Days 4-7)

**Objective:** Replace monolithic scraper with platform-specific collectors that extract structured metadata.

### Commits

#### 2.1 Collector base and browser
- **Rationale:** Define collector protocol, migrate `HumanBrowser` class
- **Files changed:**
  - `src/review_intel/collectors/base.py` — `BaseCollector` protocol
  - `src/review_intel/collectors/browser.py` — migrated `HumanBrowser` with improvements (retry, error typing)
  - `src/review_intel/collectors/registry.py` — collector factory
- **Impact:** Clean extension point for new platforms

#### 2.2 G2 collector
- **Rationale:** G2 is the richest source for B2B SaaS reviews with structured pros/cons, ratings, reviewer roles
- **Files changed:**
  - `src/review_intel/collectors/g2.py` — full structured extraction (rating, date, reviewer, role, company size, pros, cons, title)
- **Impact:** Highest-quality review data source operational

#### 2.3 Capterra collector
- **Rationale:** Capterra has high volume and structured review format
- **Files changed:**
  - `src/review_intel/collectors/capterra.py` — structured extraction
- **Impact:** Second major data source

#### 2.4 Trustpilot, Product Hunt, Gartner collectors
- **Rationale:** Cover remaining priority platforms
- **Files changed:**
  - `src/review_intel/collectors/trustpilot.py`
  - `src/review_intel/collectors/product_hunt.py`
  - `src/review_intel/collectors/gartner.py`
- **Impact:** Full platform coverage

#### 2.5 Google and community collectors
- **Rationale:** Preserve existing Google search capability, add community scraping
- **Files changed:**
  - `src/review_intel/collectors/google.py` — refactored from current `scraper.py`
  - `src/review_intel/collectors/community.py` — Reddit/forum scraping
- **Impact:** Fallback collection for platforms without direct collectors

#### 2.6 Collection integration tests
- **Files changed:**
  - `tests/integration/test_collection_pipeline.py`
- **Impact:** Verified collection layer

---

## Milestone 3 — Processing Layer (Days 8-10)

**Objective:** Build review cleaning and normalization pipeline.

### Commits

#### 3.1 Processing pipeline framework
- **Rationale:** Composable processing steps with statistics tracking
- **Files changed:**
  - `src/review_intel/processors/pipeline.py` — `ReviewPipeline` orchestrator
  - `src/review_intel/processors/__init__.py` — default pipeline factory
- **Impact:** Pluggable processing architecture

#### 3.2 Deduplication
- **Rationale:** Cross-platform deduplication is critical — same review may appear on multiple sources
- **Files changed:**
  - `src/review_intel/processors/deduplicator.py` — exact match + fuzzy (SimHash/MinHash) deduplication
- **Impact:** Eliminates inflated counts and biased analysis

#### 3.3 Quality, spam, and language processing
- **Rationale:** Filter low-quality, bot-generated, and non-English reviews
- **Files changed:**
  - `src/review_intel/processors/spam_detector.py` — heuristic + ML spam detection
  - `src/review_intel/processors/language_detector.py` — language detection with `langdetect`
  - `src/review_intel/processors/quality_scorer.py` — review quality scoring (length, specificity, coherence)
  - `src/review_intel/processors/normalizer.py` — text normalization
  - `src/review_intel/processors/profanity_handler.py` — profanity handling
- **Impact:** Clean, high-quality review corpus

#### 3.4 Processing tests
- **Files changed:**
  - `tests/unit/test_processors.py`
- **Impact:** Verified processing pipeline

---

## Milestone 4 — Analysis Layer (Days 11-17)

**Objective:** Build multi-step LLM analysis chain with structured outputs and confidence scoring.

### Commits

#### 4.1 LLM client abstraction
- **Rationale:** Unified interface for all LLM providers with structured output enforcement
- **Files changed:**
  - `src/review_intel/analysis/llm/base.py` — `BaseLLMClient` protocol
  - `src/review_intel/analysis/llm/openai_client.py` — OpenAI with JSON mode
  - `src/review_intel/analysis/llm/anthropic_client.py` — Anthropic with tool use for structured output
  - `src/review_intel/analysis/llm/ollama_client.py` — Ollama local models
  - `src/review_intel/analysis/llm/structured.py` — Pydantic model → JSON schema → validated response
- **Impact:** Reliable structured LLM outputs, zero free-form responses

#### 4.2 Analysis chain framework
- **Rationale:** Multi-step reasoning architecture with context passing
- **Files changed:**
  - `src/review_intel/analysis/chain.py` — `AnalysisChain` orchestrator
  - `src/review_intel/analysis/steps/__init__.py`
- **Impact:** Chained reasoning with validated intermediate results

#### 4.3 Analysis steps 1-3: Extraction
- **Rationale:** Core extraction steps — raw data, themes, pain points
- **Files changed:**
  - `src/review_intel/analysis/steps/raw_extraction.py` — structured fact extraction from reviews
  - `src/review_intel/analysis/steps/theme_extraction.py` — WABA theme identification
  - `src/review_intel/analysis/steps/pain_point_extraction.py` — categorized pain point extraction
- **Impact:** Structured extraction with WABA domain awareness

#### 4.4 Analysis steps 4-5: Intelligence
- **Rationale:** Higher-order analysis — feature requests, competitive intelligence
- **Files changed:**
  - `src/review_intel/analysis/steps/feature_request_extraction.py` — pattern-based + LLM feature request detection
  - `src/review_intel/analysis/steps/competitive_intel.py` — competitor strength/weakness analysis
- **Impact:** Actionable intelligence generation

#### 4.5 Analysis steps 6-7: Synthesis
- **Rationale:** Roadmap opportunities and executive summary
- **Files changed:**
  - `src/review_intel/analysis/steps/roadmap_opportunities.py` — impact-scored roadmap suggestions
  - `src/review_intel/analysis/steps/executive_summary.py` — evidence-backed executive summary
- **Impact:** Decision-ready output

#### 4.6 Confidence scoring and evidence linking
- **Rationale:** Every insight must carry a confidence score and link to source reviews
- **Files changed:**
  - `src/review_intel/analysis/confidence.py` — multi-factor confidence scoring
  - `src/review_intel/analysis/evidence_linker.py` — link insights to review IDs with quotes
- **Impact:** Evidence-backed, trustworthy insights

#### 4.7 WABA context and classifier
- **Rationale:** Inject WABA domain knowledge into LLM prompts and classify reviews
- **Files changed:**
  - `src/review_intel/analysis/waba_context.py` — domain context builder for LLM prompts
  - `src/review_intel/domain/waba_classifier.py` — automatic WABA concept tagging
- **Impact:** Domain-aware analysis

#### 4.8 Review clustering
- **Rationale:** Group similar reviews using embeddings for pattern discovery
- **Files changed:**
  - `src/review_intel/analysis/clustering/review_clusterer.py` — HDBSCAN/KMeans clustering with auto-titling
- **Impact:** Automatic theme discovery

#### 4.9 Analysis tests
- **Files changed:**
  - `tests/unit/test_analysis_steps.py`
  - `tests/unit/test_confidence.py`
  - `tests/unit/test_waba_classifier.py`
  - `tests/unit/test_evidence_linker.py`
  - `tests/integration/test_analysis_chain.py`
- **Impact:** Verified analysis pipeline

---

## Milestone 5 — Competitor Intelligence (Days 18-20)

**Objective:** Build cross-competitor analysis and benchmarking framework.

### Commits

#### 5.1 Competitor profiler
- **Files changed:**
  - `src/review_intel/intelligence/competitor_profiler.py` — build comprehensive competitor profiles
  - `src/review_intel/intelligence/waba_ecosystem.py` — WABA-specific competitive analysis
- **Impact:** Individual competitor profiles with evidence

#### 5.2 Comparison engine and switching analysis
- **Files changed:**
  - `src/review_intel/intelligence/comparison_engine.py` — multi-dimensional competitor comparison
  - `src/review_intel/intelligence/switching_analyzer.py` — detect and analyze switching patterns
  - `src/review_intel/intelligence/market_mapper.py` — competitive landscape mapping
- **Impact:** Cross-competitor intelligence

#### 5.3 Competitor intelligence tests
- **Files changed:**
  - `tests/integration/test_competitor_intel.py`
  - `docs/competitor-intelligence-framework.md`
- **Impact:** Verified competitor intelligence

---

## Milestone 6 — Delivery & Integration (Days 21-25)

**Objective:** Build delivery layer, API, dashboard, and evaluation framework.

### Commits

#### 6.1 API layer
- **Files changed:**
  - `src/review_intel/api/routes.py` — RESTful API with structured responses
  - `src/review_intel/api/dependencies.py` — FastAPI dependency injection
  - `src/review_intel/main.py` — app factory
- **Impact:** Production-ready API

#### 6.2 Dashboard and reports
- **Files changed:**
  - `src/review_intel/delivery/dashboard.py` — redesigned HTML dashboard
  - `src/review_intel/delivery/pdf_report.py` — improved PDF with evidence sections
  - `src/review_intel/delivery/api_responses.py` — Pydantic response models
- **Impact:** Rich visualization and export

#### 6.3 Gradio UI
- **Files changed:**
  - `src/review_intel/ui/gradio_app.py` — redesigned UI with competitor intelligence tabs
- **Impact:** User-facing interface

#### 6.4 Evaluation framework
- **Files changed:**
  - `tests/evaluation/benchmark_extraction.py`
  - `tests/evaluation/benchmark_sentiment.py`
  - `tests/evaluation/benchmark_hallucination.py`
  - `tests/evaluation/benchmark_dedup.py`
  - `tests/evaluation/datasets/` — gold standard test data
  - `docs/benchmark-results.md`
- **Impact:** Measurable quality metrics

#### 6.5 Documentation finalization
- **Files changed:**
  - `docs/improvement-roadmap.md` — this document, updated with results
  - `README.md` — updated with new architecture
- **Impact:** Complete documentation

---

## Gap Analysis Summary

| Capability | Current State | Target State | Gap Severity |
|---|---|---|---|
| Review metadata extraction | Text-only | 14+ fields per review | 🔴 Critical |
| Platform-specific collectors | Generic DOM scraping | 6 platform-specific collectors | 🔴 Critical |
| Structured LLM output | Free-text markdown | Pydantic-validated JSON | 🔴 Critical |
| Multi-step analysis | 2-step (chunk + synthesize) | 7-step chained reasoning | 🔴 Critical |
| WABA domain knowledge | None | Full taxonomy + classifier | 🔴 Critical |
| Confidence scoring | None | Multi-factor 0-100 scoring | 🔴 Critical |
| Evidence linking | Post-hoc search, unlinked | Review-level evidence per insight | 🔴 Critical |
| Competitor intelligence | None | Profiles, comparisons, switching analysis | 🔴 Critical |
| Deduplication | None | Exact + fuzzy dedup | 🟠 Major |
| Spam/bot detection | None | Heuristic + ML detection | 🟠 Major |
| Async pipeline | Sequential blocking | Async with concurrency control | 🟠 Major |
| Raw data persistence | None (vector store only) | SQLite raw store | 🟠 Major |
| Feature request extraction | None | Pattern + LLM extraction | 🟠 Major |
| Review clustering | None | Embedding-based clustering | 🟠 Major |
| Testing | Zero tests | Unit + integration + evaluation | 🟠 Major |
| Retry / rate limiting | None | Exponential backoff + rate limiting | 🟡 Minor |
| Cost tracking | None | Token usage tracking | 🟡 Minor |
| Excel export | None | Excel with charts | 🟡 Minor |

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Review site DOM changes | Site-specific selectors in config, not code. Fallback to generic extraction. |
| LLM hallucination | Multi-step chain, structured outputs, evidence linking, confidence scoring |
| CAPTCHA/blocking | Rate limiting, proxy rotation, browser fingerprint rotation, fallback collectors |
| API cost overrun | Batching, caching, token budgets, cost tracking |
| Schema evolution | Pydantic v2 migrations, backward-compatible schema changes |
| Data loss | Raw data persistence in SQLite, no destructive operations |

---

## Success Criteria

1. **Extraction accuracy:** ≥85% of available metadata fields populated for G2/Capterra reviews
2. **Sentiment consistency:** ≥90% agreement with gold-standard labels on benchmark dataset
3. **Hallucination rate:** <5% of generated insights unsubstantiated by source reviews
4. **Deduplication rate:** ≥95% of cross-platform duplicates detected
5. **Feature request extraction:** ≥80% recall on known feature request benchmark
6. **End-to-end latency:** <5 minutes for 1,000 reviews across 5 competitors
7. **Evidence coverage:** 100% of insights linked to ≥1 source review
