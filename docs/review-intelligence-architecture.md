# Review Intelligence Architecture

**Version:** 2.0  
**Status:** Design Phase  
**Target:** WABA & SaaS Customer Intelligence Platform

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        REVIEW INTELLIGENCE PLATFORM                  │
├──────────────────┬──────────────────┬──────────────────┬─────────────┤
│   Collection     │   Processing     │   Analysis       │  Delivery   │
│   Layer          │   Layer          │   Layer           │  Layer      │
├──────────────────┼──────────────────┼──────────────────┼─────────────┤
│ • G2 Collector   │ • Deduplicator   │ • Sentiment      │ • Dashboard │
│ • Capterra       │ • Spam Detector  │ • Theme Extract  │ • PDF/Excel │
│ • Trustpilot     │ • Language Det.  │ • Pain Points    │ • API       │
│ • Product Hunt   │ • Translator     │ • Feature Reqs   │ • Webhooks  │
│ • Gartner        │ • Quality Scorer │ • Competitor     │             │
│ • Google Search  │ • Normalizer     │ • Clustering     │             │
│ • Community      │                  │ • Benchmarking   │             │
├──────────────────┴──────────────────┴──────────────────┴─────────────┤
│                        Infrastructure Layer                          │
│  Vector Store (Qdrant) │ Raw DB (SQLite/PG) │ Cache │ Task Queue     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 1. Domain Model

### 1.1 Core Entities

```python
# schemas/review.py
class ReviewSchema(BaseModel):
    """Normalized review from any platform."""
    id: str                                 # UUID
    text: str                               # Review body
    title: str | None = None                # Review title
    rating: float | None = None             # Normalized 0-5
    date: datetime | None = None            # Review date
    reviewer_name: str | None = None
    reviewer_role: str | None = None        # e.g. "Marketing Manager"
    company_size: str | None = None         # e.g. "51-200 employees"
    industry: str | None = None
    verified: bool = False
    helpful_votes: int = 0
    country: str | None = None
    platform: Platform                      # Enum: G2, CAPTERRA, TRUSTPILOT, etc.
    platform_review_id: str | None = None   # Original ID on platform
    review_url: str | None = None
    competitor_name: str                    # The product being reviewed
    product_category: str | None = None
    pros: str | None = None                 # Separated pros (G2/Capterra)
    cons: str | None = None                 # Separated cons (G2/Capterra)
    raw_html: str | None = None             # Preserved for reprocessing
    collected_at: datetime                  # When we scraped it
    
class Platform(str, Enum):
    G2 = "g2"
    CAPTERRA = "capterra"
    TRUSTPILOT = "trustpilot"
    PRODUCT_HUNT = "product_hunt"
    GARTNER = "gartner"
    GOOGLE = "google"
    COMMUNITY = "community"
```

### 1.2 Analysis Entities

```python
# schemas/analysis.py
class SentimentCategory(str, Enum):
    SATISFACTION = "satisfaction"
    FRUSTRATION = "frustration"
    DELIGHT = "delight"
    TRUST = "trust"
    VALUE_FOR_MONEY = "value_for_money"
    EASE_OF_USE = "ease_of_use"
    ONBOARDING = "onboarding"
    SUPPORT = "support"
    RELIABILITY = "reliability"
    PERFORMANCE = "performance"
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"

class WABATheme(str, Enum):
    BROADCAST_CAMPAIGNS = "broadcast_campaigns"
    TEMPLATE_MANAGEMENT = "template_management"
    TEMPLATE_APPROVALS = "template_approvals"
    CTWA_WORKFLOWS = "ctwa_workflows"
    SHARED_INBOX = "shared_inbox"
    CHATBOT_BUILDER = "chatbot_builder"
    FLOW_BUILDER = "flow_builder"
    INTEGRATIONS = "integrations"
    CRM_SYNC = "crm_sync"
    CATALOG_SUPPORT = "catalog_support"
    COMMERCE = "commerce"
    AUTOMATION = "automation"
    WEBHOOKS = "webhooks"
    API_RELIABILITY = "api_reliability"
    MULTI_AGENT = "multi_agent"
    REPORTING = "reporting"
    PRICING = "pricing"
    ONBOARDING = "onboarding"

class ThemeAnalysis(BaseModel):
    theme: WABATheme
    frequency: int
    sentiment_score: float          # -1.0 to 1.0
    trend_direction: Literal["improving", "stable", "declining"]
    severity_score: float           # 0-100
    supporting_reviews: list[ReviewEvidence]

class PainPoint(BaseModel):
    description: str
    category: SentimentCategory
    frequency: int
    severity: float                 # 0-100
    business_impact: str
    supporting_reviews: list[ReviewEvidence]
    confidence_score: float         # 0-100

class FeatureRequest(BaseModel):
    description: str
    frequency: int
    sentiment_score: float
    urgency: Literal["low", "medium", "high", "critical"]
    supporting_evidence: list[ReviewEvidence]
    confidence_score: float

class ReviewEvidence(BaseModel):
    review_id: str
    source: Platform
    quote: str
    review_url: str | None = None
    review_date: datetime | None = None

class ReviewCluster(BaseModel):
    cluster_id: str
    title: str
    summary: str
    sample_reviews: list[ReviewEvidence]
    sentiment_score: float
    confidence_score: float
    review_count: int

class Insight(BaseModel):
    """Every generated insight must carry evidence and confidence."""
    id: str
    insight_type: Literal["pain_point", "feature_request", "strength", 
                           "weakness", "opportunity", "trend"]
    title: str
    description: str
    confidence_score: float         # 0-100
    evidence: list[ReviewEvidence]
    metadata: dict = {}
```

### 1.3 Competitor Intelligence Entities

```python
# schemas/competitor.py
class CompetitorProfile(BaseModel):
    name: str
    platform_category: str          # e.g. "WhatsApp BSP"
    total_reviews: int
    average_rating: float
    strengths: list[Insight]
    weaknesses: list[Insight]
    feature_gaps: list[Insight]
    market_opportunities: list[Insight]
    
class CompetitorComparison(BaseModel):
    competitors: list[str]
    dimensions: list[ComparisonDimension]
    switching_patterns: list[SwitchingPattern]
    
class ComparisonDimension(BaseModel):
    dimension: str                  # e.g. "Customer Support"
    scores: dict[str, float]        # competitor_name → score
    evidence: dict[str, list[ReviewEvidence]]

class SwitchingPattern(BaseModel):
    from_product: str
    to_product: str
    reasons: list[str]
    frequency: int
    evidence: list[ReviewEvidence]
```

---

## 2. Architecture Layers

### 2.1 Collection Layer

```
collectors/
├── __init__.py
├── base.py              # Abstract BaseCollector protocol
├── g2.py                # G2 collector with structured extraction
├── capterra.py          # Capterra collector
├── trustpilot.py        # Trustpilot collector
├── product_hunt.py      # Product Hunt collector
├── gartner.py           # Gartner Peer Insights collector
├── google.py            # Google search fallback collector
├── community.py         # Reddit/forum collector
└── registry.py          # Collector registry & factory
```

**Base Collector Protocol:**
```python
class BaseCollector(Protocol):
    platform: Platform
    
    async def collect(
        self, 
        company: str, 
        max_reviews: int = 200,
        since: datetime | None = None,
    ) -> list[ReviewSchema]: ...
    
    async def health_check(self) -> bool: ...
```

Each collector knows its platform's DOM structure, extracts all available metadata (rating, date, reviewer, pros/cons), handles pagination, and returns normalized `ReviewSchema` objects.

### 2.2 Processing Layer

```
processors/
├── __init__.py
├── pipeline.py          # Orchestrates processing steps
├── deduplicator.py      # Exact + fuzzy deduplication
├── spam_detector.py     # Bot/spam review detection
├── language_detector.py # Language detection + filtering
├── translator.py        # Translation pipeline
├── quality_scorer.py    # Review quality scoring
├── normalizer.py        # Text normalization
└── profanity_handler.py # Profanity detection + handling
```

**Processing Pipeline:**
```python
class ReviewPipeline:
    def __init__(self, steps: list[ProcessingStep]):
        self.steps = steps
    
    async def process(self, reviews: list[ReviewSchema]) -> ProcessingResult:
        result = ProcessingResult(input_count=len(reviews))
        for step in self.steps:
            reviews = await step.process(reviews)
            result.step_results[step.name] = step.stats
        result.output = reviews
        return result
```

### 2.3 Analysis Layer — Multi-Step LLM Chain

```
analysis/
├── __init__.py
├── chain.py             # Analysis chain orchestrator
├── steps/
│   ├── __init__.py
│   ├── raw_extraction.py       # Step 1: Extract structured data
│   ├── theme_extraction.py     # Step 2: Identify themes
│   ├── pain_point_extraction.py # Step 3: Extract pain points
│   ├── feature_request_extraction.py # Step 4: Feature requests
│   ├── competitive_intel.py    # Step 5: Competitive intelligence
│   ├── roadmap_opportunities.py # Step 6: Roadmap suggestions
│   └── executive_summary.py    # Step 7: Executive summary
├── llm/
│   ├── __init__.py
│   ├── base.py          # Abstract LLM client
│   ├── openai_client.py
│   ├── anthropic_client.py
│   ├── ollama_client.py
│   └── structured.py   # Structured output enforcement
├── clustering/
│   ├── __init__.py
│   └── review_clusterer.py  # Embedding-based clustering
├── confidence.py        # Confidence scoring engine
├── waba_context.py      # WABA domain knowledge & classifiers
└── evidence_linker.py   # Link insights to source reviews
```

**Analysis Chain:**
```python
class AnalysisChain:
    """Multi-step analysis with chained reasoning."""
    
    def __init__(self, llm: BaseLLMClient, vector_store: VectorStore):
        self.steps = [
            RawExtractionStep(llm),
            ThemeExtractionStep(llm),
            PainPointExtractionStep(llm),
            FeatureRequestExtractionStep(llm),
            CompetitiveIntelStep(llm),
            RoadmapOpportunityStep(llm),
            ExecutiveSummaryStep(llm),
        ]
    
    async def analyze(
        self, 
        reviews: list[ReviewSchema], 
        company: str,
    ) -> AnalysisResult:
        context = AnalysisContext(reviews=reviews, company=company)
        for step in self.steps:
            context = await step.execute(context)
        return context.to_result()
```

**Every step produces Pydantic-validated output:**
```python
class AnalysisStep(Protocol):
    name: str
    
    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        """Execute step, validate output with Pydantic, update context."""
        ...
```

### 2.4 Vector Store Layer

```
store/
├── __init__.py
├── base.py              # Abstract VectorStore protocol
├── qdrant_store.py      # Qdrant implementation
├── chroma_store.py      # ChromaDB fallback
├── raw_store.py         # SQLite/PostgreSQL raw review storage
└── cache.py             # Redis/in-memory cache
```

**Embeddings stored:**
- Review embeddings (for similarity search)
- Theme embeddings (for theme clustering)
- Feature request embeddings (for request deduplication)
- Insight embeddings (for insight retrieval)

### 2.5 Competitor Intelligence Layer

```
intelligence/
├── __init__.py
├── competitor_profiler.py    # Build competitor profiles
├── comparison_engine.py      # Cross-competitor analysis
├── switching_analyzer.py     # Why users switch between products
├── market_mapper.py          # Map competitive landscape
└── waba_ecosystem.py         # WABA-specific ecosystem intelligence
```

### 2.6 Delivery Layer

```
delivery/
├── __init__.py
├── dashboard.py         # HTML dashboard renderer
├── pdf_report.py        # PDF report generator
├── excel_export.py      # Excel export with charts
├── api_responses.py     # Structured API response models
└── templates/           # Report templates
```

---

## 3. WABA Domain Model

```
domain/
├── __init__.py
├── waba_taxonomy.py     # WABA concept taxonomy
├── waba_classifier.py   # Classify reviews by WABA concepts
├── platform_registry.py # Target platform metadata
└── ecosystem_context.py # WhatsApp ecosystem context for LLM
```

**WhatsApp Business Concept Taxonomy:**
```python
WABA_CONCEPTS = {
    "messaging": [
        "WhatsApp Cloud API", "On-Premise API", "Business API",
        "Conversation Categories", "Marketing Messages", 
        "Utility Messages", "Authentication Messages",
        "Service Conversations",
    ],
    "templates": [
        "Template Management", "Template Approvals", "Template Categories",
        "Header Templates", "Interactive Templates", "Authentication Templates",
        "Utility Templates", "Marketing Templates",
    ],
    "commerce": [
        "Catalog Support", "Product Messages", "Order Messages",
        "Payment Integration", "Commerce Messaging",
    ],
    "engagement": [
        "Broadcast Campaigns", "CTWA Ads", "Click-to-WhatsApp",
        "Flow Messages", "WhatsApp Flows", "Interactive Messages",
        "Quick Replies", "List Messages", "CTA Buttons",
    ],
    "platform": [
        "Embedded Signup", "Business Verification", "Phone Number Migration",
        "Quality Rating", "Messaging Limits", "Webhook Configuration",
        "API Reliability", "Rate Limiting",
    ],
    "operations": [
        "Shared Team Inbox", "Multi-Agent Support", "Agent Assignment",
        "Chatbot Builder", "Flow Builder", "Automation Rules",
        "CRM Synchronization", "Contact Management",
    ],
    "analytics": [
        "Conversation Analytics", "Campaign Analytics", "Agent Performance",
        "Message Delivery", "Read Receipts", "Response Time Tracking",
    ],
}
```

---

## 4. Data Flow

```
                    ┌──────────┐
                    │  Target  │
                    │Companies │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │Collection│──→ Raw JSON (preserved)
                    │  Layer   │
                    └────┬─────┘
                         │ list[ReviewSchema]
                    ┌────▼─────┐
                    │Processing│──→ Dedup stats, quality scores
                    │ Pipeline │
                    └────┬─────┘
                         │ list[ReviewSchema] (cleaned)
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
         │Raw DB  │ │Vector  │ │Analysis│
         │(SQLite)│ │Store   │ │Chain   │
         └────────┘ │(Qdrant)│ └───┬────┘
                    └────────┘     │
                         │         │ AnalysisResult
                    ┌────▼─────────▼──┐
                    │Evidence Linker  │
                    └────┬────────────┘
                         │ Evidence-backed insights
                    ┌────▼─────┐
                    │Competitor│
                    │  Intel   │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Delivery │──→ Dashboard, PDF, API, Excel
                    │  Layer   │
                    └──────────┘
```

---

## 5. Confidence Scoring Model

Every insight receives a confidence score (0-100) computed from:

| Factor | Weight | Description |
|---|---|---|
| Review volume | 25% | More reviews → higher confidence |
| Source agreement | 25% | Multiple platforms agree → higher |
| Sentiment consistency | 20% | Reviews agree on sentiment direction |
| Source quality | 15% | Verified reviews, reputable platforms score higher |
| Evidence strength | 15% | Direct quotes vs. inferred themes |

```python
def compute_confidence(
    review_count: int,
    source_count: int,
    sentiment_variance: float,
    verified_ratio: float,
    evidence_directness: float,
) -> float:
    volume_score = min(review_count / 10, 1.0) * 25
    agreement_score = min(source_count / 3, 1.0) * 25
    consistency_score = (1 - sentiment_variance) * 20
    quality_score = verified_ratio * 15
    evidence_score = evidence_directness * 15
    return round(volume_score + agreement_score + consistency_score 
                 + quality_score + evidence_score, 1)
```

---

## 6. Scalability Design

### Async Pipeline with Concurrency Control

```python
class ScalablePipeline:
    def __init__(self, max_concurrent_scrapes: int = 5,
                 max_concurrent_llm_calls: int = 3):
        self.scrape_semaphore = asyncio.Semaphore(max_concurrent_scrapes)
        self.llm_semaphore = asyncio.Semaphore(max_concurrent_llm_calls)
    
    async def run(self, companies: list[str]):
        tasks = [self._process_company(c) for c in companies]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_company(self, company: str):
        async with self.scrape_semaphore:
            reviews = await self.collect(company)
        processed = await self.process(reviews)
        async with self.llm_semaphore:
            analysis = await self.analyze(processed)
        return analysis
```

### Batching Strategy

| Review Count | Batch Size | Concurrency | Expected Time |
|---|---|---|---|
| 10 | 10 (single) | 1 | 5-10s |
| 100 | 25 | 2 | 20-40s |
| 1,000 | 50 | 3 | 2-5 min |
| 10,000+ | 100 | 5 | 10-20 min |

---

## 7. Directory Structure

```
scrapper-agent/
├── src/
│   └── review_intel/
│       ├── __init__.py
│       ├── config.py                # Settings via pydantic-settings
│       ├── main.py                  # FastAPI app factory
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── review.py            # ReviewSchema, Platform enum
│       │   ├── analysis.py          # All analysis result models
│       │   ├── competitor.py        # Competitor intelligence models
│       │   └── waba.py              # WABA-specific enums/models
│       ├── collectors/
│       │   ├── __init__.py
│       │   ├── base.py              # BaseCollector protocol
│       │   ├── browser.py           # HumanBrowser (reused)
│       │   ├── g2.py
│       │   ├── capterra.py
│       │   ├── trustpilot.py
│       │   ├── product_hunt.py
│       │   ├── gartner.py
│       │   ├── google.py
│       │   ├── community.py
│       │   └── registry.py
│       ├── processors/
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   ├── deduplicator.py
│       │   ├── spam_detector.py
│       │   ├── language_detector.py
│       │   ├── translator.py
│       │   ├── quality_scorer.py
│       │   ├── normalizer.py
│       │   └── profanity_handler.py
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── chain.py
│       │   ├── steps/
│       │   │   ├── __init__.py
│       │   │   ├── raw_extraction.py
│       │   │   ├── theme_extraction.py
│       │   │   ├── pain_point_extraction.py
│       │   │   ├── feature_request_extraction.py
│       │   │   ├── competitive_intel.py
│       │   │   ├── roadmap_opportunities.py
│       │   │   └── executive_summary.py
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── openai_client.py
│       │   │   ├── anthropic_client.py
│       │   │   ├── ollama_client.py
│       │   │   └── structured.py
│       │   ├── clustering/
│       │   │   ├── __init__.py
│       │   │   └── review_clusterer.py
│       │   ├── confidence.py
│       │   ├── waba_context.py
│       │   └── evidence_linker.py
│       ├── intelligence/
│       │   ├── __init__.py
│       │   ├── competitor_profiler.py
│       │   ├── comparison_engine.py
│       │   ├── switching_analyzer.py
│       │   ├── market_mapper.py
│       │   └── waba_ecosystem.py
│       ├── store/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── vector_store.py
│       │   ├── raw_store.py
│       │   └── cache.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── waba_taxonomy.py
│       │   ├── waba_classifier.py
│       │   ├── platform_registry.py
│       │   └── ecosystem_context.py
│       ├── delivery/
│       │   ├── __init__.py
│       │   ├── dashboard.py
│       │   ├── pdf_report.py
│       │   ├── api_responses.py
│       │   └── templates/
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── dependencies.py
│       └── ui/
│           ├── __init__.py
│           └── gradio_app.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_schemas.py
│   │   ├── test_processors.py
│   │   ├── test_analysis_steps.py
│   │   ├── test_confidence.py
│   │   ├── test_waba_classifier.py
│   │   └── test_evidence_linker.py
│   ├── integration/
│   │   ├── test_collection_pipeline.py
│   │   ├── test_analysis_chain.py
│   │   └── test_competitor_intel.py
│   └── evaluation/
│       ├── __init__.py
│       ├── benchmark_extraction.py
│       ├── benchmark_sentiment.py
│       ├── benchmark_hallucination.py
│       ├── benchmark_dedup.py
│       ├── datasets/
│       │   ├── gold_standard_reviews.json
│       │   ├── labeled_sentiments.json
│       │   └── known_feature_requests.json
│       └── results/
├── docs/
│   ├── audit.md
│   ├── review-intelligence-architecture.md
│   ├── improvement-roadmap.md
│   ├── benchmark-results.md
│   ├── waba-domain-model.md
│   └── competitor-intelligence-framework.md
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```
