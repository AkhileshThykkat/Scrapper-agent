# Benchmark Results

**Status:** Pending — evaluation framework under development  
**Last Updated:** 2026-06-02

---

## 1. Evaluation Metrics

### 1.1 Extraction Accuracy

| Metric | Target | Current | Status |
|---|---|---|---|
| Rating extraction accuracy | ≥95% | N/A (not extracted) | 🔴 Not implemented |
| Date extraction accuracy | ≥90% | N/A (not extracted) | 🔴 Not implemented |
| Reviewer name extraction | ≥85% | N/A (not extracted) | 🔴 Not implemented |
| Pros/cons separation (G2) | ≥90% | N/A (not extracted) | 🔴 Not implemented |
| Review text extraction | ≥80% | ~60% (estimated) | 🟡 Baseline |

### 1.2 Sentiment Consistency

| Metric | Target | Current | Status |
|---|---|---|---|
| Positive/negative classification | ≥90% | N/A | 🔴 Not measured |
| Multi-category sentiment | ≥85% | N/A | 🔴 Not measured |
| Cross-LLM consistency | ≥80% | N/A | 🔴 Not measured |

### 1.3 Theme Extraction

| Metric | Target | Current | Status |
|---|---|---|---|
| WABA theme detection recall | ≥85% | N/A | 🔴 Not implemented |
| Theme precision | ≥80% | N/A | 🔴 Not implemented |
| Theme consistency across runs | ≥90% | N/A | 🔴 Not measured |

### 1.4 Hallucination Rate

| Metric | Target | Current | Status |
|---|---|---|---|
| Unsubstantiated claims | <5% | ~15-25% (estimated) | 🔴 High risk |
| Fabricated statistics | 0% | Unknown | 🔴 Not measured |
| Misattributed evidence | <3% | Unknown | 🔴 Not measured |

### 1.5 Deduplication

| Metric | Target | Current | Status |
|---|---|---|---|
| Exact duplicate detection | 100% | ~70% (text match) | 🟡 Partial |
| Fuzzy duplicate detection | ≥95% | 0% | 🔴 Not implemented |
| False positive rate | <2% | N/A | 🔴 Not measured |

### 1.6 Feature Request Extraction

| Metric | Target | Current | Status |
|---|---|---|---|
| Feature request recall | ≥80% | 0% | 🔴 Not implemented |
| Feature request precision | ≥75% | 0% | 🔴 Not implemented |
| Urgency classification accuracy | ≥70% | 0% | 🔴 Not implemented |

---

## 2. Performance Benchmarks

### 2.1 Latency

| Operation | Target | Current | Status |
|---|---|---|---|
| 10 reviews, single company | <10s | ~30s | 🟠 Slow |
| 100 reviews, single company | <60s | ~5-10 min | 🔴 Very slow |
| 1,000 reviews, single company | <5 min | N/A (not tested) | 🔴 Unknown |
| 10,000+ reviews | <20 min | N/A | 🔴 Unknown |

### 2.2 Cost

| Operation | Target | Current | Status |
|---|---|---|---|
| Cost per 100 reviews (GPT-4o) | <$0.50 | ~$1-2 (estimated) | 🟠 Over budget |
| Cost per 100 reviews (Claude) | <$0.50 | ~$0.80 (estimated) | 🟡 Acceptable |
| Cost per 100 reviews (Ollama) | $0 | $0 | ✅ Free |

### 2.3 Throughput

| Metric | Target | Current | Status |
|---|---|---|---|
| Reviews/minute (scraping) | 50 | ~5-10 | 🔴 Low |
| Reviews/minute (analysis) | 200 | ~20-40 | 🟠 Low |
| Concurrent companies | 5 | 1 | 🔴 Sequential only |

---

## 3. Gold Standard Datasets

### 3.1 Required Datasets (To Be Created)

| Dataset | Purpose | Size | Status |
|---|---|---|---|
| `gold_standard_reviews.json` | Known reviews with all metadata fields | 200 reviews | 🔴 Pending |
| `labeled_sentiments.json` | Human-labeled sentiment per review | 100 reviews | 🔴 Pending |
| `known_feature_requests.json` | Human-identified feature requests | 50 items | 🔴 Pending |
| `known_pain_points.json` | Human-identified pain points | 50 items | 🔴 Pending |
| `duplicate_pairs.json` | Known duplicate review pairs | 30 pairs | 🔴 Pending |
| `waba_theme_labels.json` | Human-labeled WABA themes | 100 reviews | 🔴 Pending |

---

## 4. Evaluation Protocol

### 4.1 Extraction Accuracy Test

1. Scrape reviews from G2/Capterra for a known company
2. Manually verify extracted fields against source page
3. Calculate per-field accuracy: `correct / total`

### 4.2 Sentiment Consistency Test

1. Run sentiment analysis 3 times on the same review set
2. Compare outputs across runs
3. Measure inter-run agreement (Cohen's Kappa or % agreement)

### 4.3 Hallucination Detection Test

1. Run full analysis pipeline on gold standard dataset
2. For each generated insight, verify against source reviews
3. Flag insights with no supporting evidence as hallucinations
4. Calculate: `hallucinations / total_insights`

### 4.4 End-to-End Test

1. Scrape 100 reviews for a WABA platform
2. Run full pipeline: collection → processing → analysis → delivery
3. Measure total time, cost, and output quality

---

*This document will be updated with actual benchmark results as the evaluation framework is implemented in Milestone 6.*
