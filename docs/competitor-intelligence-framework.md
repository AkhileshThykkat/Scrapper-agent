# Competitor Intelligence Framework

**Purpose:** Systematic framework for generating actionable competitive intelligence from review data across the WABA and SaaS ecosystem.

---

## 1. Framework Overview

```
                     ┌──────────────────┐
                     │  Review Corpus   │
                     │  (per platform)  │
                     └────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         ┌────▼────┐    ┌────▼────┐    ┌─────▼─────┐
         │Strength │    │Weakness │    │  Feature   │
         │Analysis │    │Analysis │    │Gap Analysis│
         └────┬────┘    └────┬────┘    └─────┬─────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Cross-Competitor  │
                    │    Comparison      │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
         ┌────▼────┐    ┌────▼────┐    ┌─────▼─────┐
         │Switching│    │ Market  │    │  Roadmap   │
         │Patterns │    │Mapping  │    │Opportunity │
         └─────────┘    └─────────┘    └───────────┘
```

---

## 2. Individual Competitor Profiling

### 2.1 Profile Structure

For each competitor, generate:

```python
CompetitorProfile:
    name: str
    category: str                    # "BSP", "CPaaS", "CRM", "Support"
    total_reviews_analyzed: int
    review_sources: dict[Platform, int]
    overall_rating: float            # Weighted average across platforms
    rating_trend: str                # "improving" | "stable" | "declining"
    
    # Dimensional scores (0-100, evidence-backed)
    dimension_scores:
        ease_of_use: DimensionScore
        pricing_value: DimensionScore
        customer_support: DimensionScore
        reliability: DimensionScore
        feature_richness: DimensionScore
        integration_quality: DimensionScore
        automation_capability: DimensionScore
        analytics_quality: DimensionScore
    
    strengths: list[Insight]         # What customers consistently praise
    weaknesses: list[Insight]        # What customers consistently criticize
    feature_gaps: list[Insight]      # Features customers say are missing
    recent_trends: list[Insight]     # Changes in sentiment over time
```

### 2.2 Strength Detection

Identify strengths by looking for:
- Reviews with rating ≥4/5 mentioning specific features
- Repeated positive mentions of the same capability across reviewers
- "Best feature" or "main reason I chose" language patterns
- Reviewer segments (role, company size) that are most satisfied

**Evidence requirement:** Each strength must reference ≥3 reviews from ≥2 sources.

### 2.3 Weakness Detection

Identify weaknesses by looking for:
- Reviews with rating ≤2/5 mentioning specific issues
- Repeated complaints about the same capability
- "Dealbreaker" or "reason I'm leaving" language
- Severity indicators: "unusable", "broken", "terrible"

**Evidence requirement:** Each weakness must reference ≥3 reviews from ≥2 sources.

### 2.4 Feature Gap Detection

Identify missing features by looking for:
- "I wish they had..."
- "Missing X feature"
- "Compared to [competitor], they don't have..."
- "Would be great if..."
- "Need support for..."
- Negative reviews that specifically cite absence of functionality

---

## 3. Cross-Competitor Comparison

### 3.1 Comparison Matrix

Generate a comparison matrix across all tracked competitors:

| Dimension | Interakt | Wati | AiSensy | Gallabox | DoubleTick | ... |
|---|---|---|---|---|---|---|
| Ease of Use | 78 | 82 | 71 | 75 | 80 | ... |
| Pricing | 85 | 65 | 90 | 80 | 75 | ... |
| Support | 70 | 75 | 60 | 72 | 68 | ... |
| Reliability | 72 | 80 | 68 | 70 | 74 | ... |
| ... | ... | ... | ... | ... | ... | ... |

Each score is backed by review evidence and carries a confidence score.

### 3.2 Head-to-Head Comparison

For any two competitors, generate:

```python
HeadToHead:
    competitor_a: str
    competitor_b: str
    
    # Where A is better
    a_advantages: list[ComparisonPoint]
    
    # Where B is better
    b_advantages: list[ComparisonPoint]
    
    # Where they're equivalent
    parity_points: list[ComparisonPoint]
    
    # Switching patterns between them
    a_to_b_switches: SwitchingAnalysis
    b_to_a_switches: SwitchingAnalysis
    
    # Verdict
    summary: str
    best_for: dict[str, str]  # use_case → recommended_platform
```

### 3.3 Comparison Point Structure

```python
ComparisonPoint:
    dimension: str
    score_a: float
    score_b: float
    description: str
    evidence_a: list[ReviewEvidence]
    evidence_b: list[ReviewEvidence]
    confidence: float
```

---

## 4. Switching Pattern Analysis

### 4.1 Detection

Detect switching patterns from review language:
- "Switched from X to Y"
- "Migrated from X"
- "Previously used X"
- "Left X because..."
- "Moved to X after..."
- "Better than X in..."
- "Unlike X, this..."

### 4.2 Switching Analysis Structure

```python
SwitchingPattern:
    from_product: str
    to_product: str
    frequency: int              # Number of reviews mentioning this switch
    
    reasons:
        - reason: str
          frequency: int
          category: str         # "pricing", "features", "support", "reliability"
          evidence: list[ReviewEvidence]
    
    satisfaction_after_switch:
        average_rating: float
        sentiment_score: float
    
    confidence: float
```

### 4.3 Key Questions Answered

- **Why do users switch from Wati to Interakt?**
  - Common reasons ranked by frequency
  - Post-switch satisfaction
  
- **Why do users leave AiSensy?**
  - Top exit reasons
  - Where do they go?
  
- **Most common complaints about Gallabox?**
  - Categorized and severity-ranked
  
- **Best-rated support experience across BSPs?**
  - Ranked by support satisfaction score

---

## 5. Market Opportunity Detection

### 5.1 Opportunity Identification

Market opportunities arise from:
1. **Universal pain points:** Issues every competitor has (e.g., "template approval takes too long")
2. **Feature gaps across ecosystem:** Features no competitor offers well
3. **Emerging needs:** New requirements driven by WhatsApp platform changes
4. **Underserved segments:** Company sizes, industries, or use cases poorly served

### 5.2 Opportunity Scoring

```python
MarketOpportunity:
    title: str
    description: str
    
    # Scoring factors
    demand_score: float        # How many users want this (0-100)
    gap_score: float          # How poorly served it is today (0-100)
    feasibility_score: float  # How feasible to build (0-100, estimated)
    impact_score: float       # Potential business impact (0-100)
    
    # Composite
    opportunity_score: float  # Weighted composite
    
    # Evidence
    supporting_reviews: list[ReviewEvidence]
    affected_competitors: list[str]
    confidence: float
```

### 5.3 Opportunity Categories

| Category | Example |
|---|---|
| **Feature gap** | "No BSP offers good A/B testing for broadcasts" |
| **Quality gap** | "All BSPs have poor template approval UX" |
| **Price gap** | "No affordable option for enterprise features" |
| **Integration gap** | "Missing native CRM integrations" |
| **Segment gap** | "No BSP optimized for healthcare use cases" |
| **Ecosystem gap** | "Poor support for WhatsApp Flows across BSPs" |

---

## 6. Intelligence Output Formats

### 6.1 Executive Summary

One-page overview for leadership:
- Top 3 competitor strengths to match
- Top 3 market opportunities to pursue
- Top 3 risks from competitor improvements
- Key switching pattern (biggest flow direction)

### 6.2 Detailed Competitor Report

Per-competitor deep dive:
- Profile with dimensional scores
- All strengths with evidence
- All weaknesses with evidence
- Feature gaps
- User sentiment trends
- Switching patterns in/out

### 6.3 Competitive Landscape Map

Visual representation:
- X-axis: Pricing (affordable → expensive)
- Y-axis: Feature richness (basic → comprehensive)
- Bubble size: Review volume
- Color: Overall sentiment

### 6.4 Feature Parity Matrix

| Feature | Interakt | Wati | AiSensy | Gallabox | Your Product |
|---|---|---|---|---|---|
| Broadcast A/B testing | ❌ | ❌ | ❌ | ❌ | **Opportunity** |
| WhatsApp Flows | ✅ | ✅ | ❌ | ❌ | ? |
| Native Shopify | ✅ | ❌ | ❌ | ✅ | ? |
| Multi-channel inbox | ❌ | ✅ | ❌ | ❌ | ? |

---

## 7. Refresh Cadence

| Data | Refresh Frequency |
|---|---|
| Review collection | Weekly |
| Competitor profiles | Weekly |
| Cross-competitor comparison | Bi-weekly |
| Market opportunities | Monthly |
| Executive summary | Monthly |
| Full benchmark report | Quarterly |

---

## 8. Confidence & Quality Gates

### Minimum Evidence Thresholds

| Insight Type | Min Reviews | Min Sources | Min Confidence |
|---|---|---|---|
| Strength | 3 | 2 | 60 |
| Weakness | 3 | 2 | 60 |
| Feature gap | 5 | 2 | 65 |
| Market opportunity | 10 | 3 | 70 |
| Switching pattern | 3 | 2 | 55 |
| Executive recommendation | 15 | 3 | 75 |

Insights below these thresholds are flagged as "low confidence" and excluded from executive summaries.
