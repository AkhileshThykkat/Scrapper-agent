import logging
import os
from datetime import datetime
from typing import List, Optional

from agent.embeddings import ReviewVectorStore

logger = logging.getLogger(__name__)


def _detect_method() -> str:
    local_base = os.getenv("OLLAMA_BASE_URL", "")
    if local_base:
        model = os.getenv("LOCAL_MODEL", "gemma3:12b")
        return f"AI-powered (Ollama: {model})"
    if os.getenv("ANTHROPIC_API_KEY"):
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        return f"AI-powered (Anthropic: {model})"
    if os.getenv("OPENAI_API_KEY"):
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        return f"AI-powered (OpenAI: {model})"
    return "keyword-based (no LLM configured)"


def _llm_configured() -> bool:
    return bool(os.getenv("OLLAMA_BASE_URL") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


def _call_llm(prompt: str, system_prompt: str = "") -> str:
    """Call LLM for analysis. Supports OpenAI, Anthropic, and local models via Ollama."""
    local_base = os.getenv("OLLAMA_BASE_URL", "")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key and not local_base:
        return ""

    try:
        if local_base:
            from openai import OpenAI
            client = OpenAI(base_url=local_base.rstrip("/") + "/v1", api_key="ollama")
            model = os.getenv("LOCAL_MODEL", "gemma3:12b")
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=4096,
            )
            return response.choices[0].message.content
        elif os.getenv("ANTHROPIC_API_KEY"):
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=4000,
                system=system_prompt or "You are a professional review analyst.",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        else:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=messages,
                max_tokens=4000,
            )
            return response.choices[0].message.content
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return ""


def _fallback_analysis(reviews: list) -> str:
    """Simple keyword-based analysis on raw review texts when no LLM is available."""
    tech_keywords = ["bug", "crash", "slow", "error", "fail", "broken", "performance", "loading", "glitch", "freeze", "lag", "technical", "buggy", "glitchy", "unstable", "down"]
    ui_keywords = ["confusing", "ugly", "hard to use", "navigation", "interface", "design", "layout", "clunky", "intuitive", "mobile", "button", "menu", "dashboard", "cluttered"]
    support_keywords = ["support", "customer service", "refund", "response", "wait time", "unhelpful", "chat", "email", "phone", "billing", "rude", "unresolved", "scam", "refund", "charge", "money"]
    love_keywords = ["great", "amazing", "excellent", "wonderful", "fantastic", "love", "best", "awesome", "incredible", "perfect", "outstanding", "recommend", "easy", "fast", "reliable", "helpful", "friendly", "beautiful", "impressive", "satisfied", "happy", "thank", "brilliant", "smooth"]

    tech_lines, ui_lines, support_lines, love_lines = [], [], [], []

    for review in reviews:
        lower = review.lower()
        if any(kw in lower for kw in tech_keywords):
            tech_lines.append(review)
        if any(kw in lower for kw in ui_keywords):
            ui_lines.append(review)
        if any(kw in lower for kw in support_keywords):
            support_lines.append(review)
        if any(kw in lower for kw in love_keywords):
            love_lines.append(review)

    def fmt_section(title, lines_):
        if not lines_:
            return f"### {title}\nNo clear issues identified.\n"
        dedup = []
        seen = set()
        for l in lines_:
            if l not in seen:
                seen.add(l)
                dedup.append(l)
        return f"### {title}\n" + "\n".join(f"- {l[:300]}" for l in dedup[:10]) + "\n"

    pain_a = fmt_section("A. Technical Pain Points", tech_lines)
    pain_b = fmt_section("B. UI/UX Pain Points", ui_lines)
    pain_c = fmt_section("C. Customer Support Pain Points", support_lines)
    love_dedup = []
    seen_love = set()
    for l in love_lines:
        if l not in seen_love:
            seen_love.add(l)
            love_dedup.append(l[:300])
    love_summary = "\n".join(f"- {l}" for l in love_dedup[:12]) if love_dedup else "No clear positive themes identified."

    tech_count, ui_count, support_count = len(tech_lines), len(ui_lines), len(support_lines)
    total_pain = tech_count + ui_count + support_count
    top_cat = "Technical" if tech_count >= ui_count and tech_count >= support_count else "UI/UX" if ui_count >= tech_count and ui_count >= support_count else "Customer Support"

    return f"""## 1. Main Pain Points (Categorized)

{pain_a}
{pain_b}
{pain_c}

## 2. Most Beloved Things
{love_summary}

## 3. Overall Sentiment
Keyword-based analysis of {len(reviews)} reviews shows {total_pain} pain-related mentions and {len(love_lines)} positive mentions across categories. The top pain category is {top_cat}.

## 4. Key Statistics
- Most mentioned pain category: **{top_cat}**
- Technical mentions: {tech_count}
- UI/UX mentions: {ui_count}
- Customer Support mentions: {support_count}
- Positive mentions: {len(love_lines)}"""


def _add_header(report: str, company: str, review_count: int, method: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"""# Review Analysis Report for {company}

**Analysis Date:** {timestamp}
**Reviews Analyzed:** {review_count}
**Analysis Method:** {method}

---
"""
    return header + report


def _extract_evidence(store: ReviewVectorStore, company: str) -> dict:
    """Search vector store for review snippets in each category."""
    return {
        "technical": [r["text"] for r in store.search_reviews(
            "bug crash error slow performance broken glitch loading fail technical issue app platform feature", company=company, n_results=8
        )],
        "ui_ux": [r["text"] for r in store.search_reviews(
            "design interface navigation confusing ugly layout usability mobile app hard to use dashboard interface", company=company, n_results=8
        )],
        "support": [r["text"] for r in store.search_reviews(
            "support customer service refund help response chat email phone wait time rude team", company=company, n_results=8
        )],
        "positive": [r["text"] for r in store.search_reviews(
            "great amazing excellent love best awesome easy fast reliable happy recommend helpful", company=company, n_results=8
        )],
    }


def analyze_reviews(reviews: List[str], company: str, store: Optional[ReviewVectorStore] = None) -> str:
    """Analyze reviews and generate a structured report."""
    if not reviews:
        return f"# Review Analysis Report for {company}\n\nNo reviews found to analyze."

    method = _detect_method()
    evidence = _extract_evidence(store, company) if store else {}

    if not _llm_configured():
        return _add_header(
            _fallback_analysis(reviews) + _build_evidence_section(store, company),
            company, len(reviews), method,
        )

    chunk_size = 40
    all_analyses = []
    for i in range(0, len(reviews), chunk_size):
        chunk = reviews[i:i + chunk_size]
        reviews_text = "\n\n".join([f"[{i + j + 1}] {r}" for j, r in enumerate(chunk)])

        prompt = f"""Read these reviews for "{company}" and list exactly what you find.

## Pain Points Found
List every specific complaint mentioned. For each say which category it fits:
- Technical: if it's about bugs, crashes, errors, performance, features
- UI/UX: if it's about design, navigation, confusing interface
- Customer Support: if it's about support team, response time, help quality

## Positive Points Found
List everything positive mentioned.

## Sentiment
One sentence: are these reviews mostly positive, negative, or mixed?

Reviews:
{reviews_text}

Be brief. Only list what you actually see in the reviews above.
"""
        analysis = _call_llm(prompt, "List facts only. No fluff.")
        all_analyses.append(analysis)

    combined = "\n\n".join(a for a in all_analyses if a.strip())
    if not combined.strip():
        return _add_header(
            _fallback_analysis(reviews) + _build_evidence_section(store, company),
            company, len(reviews), method,
        )

    synthesis_prompt = f"""Combine these review batch analyses for "{company}" into one report.

CRITICAL: The analyses below DO contain findings. Read them carefully and list every pain point and every positive point. Do NOT say "none mentioned" if the analyses mention issues.

Format:
## Main Pain Points
### Technical
- list every technical issue from the analyses
### UI/UX
- every design/usability issue from the analyses
### Customer Support
- every support issue from the analyses

## Most Beloved Things
- every positive point

## Overall Sentiment
One paragraph.

## Key Statistics
- Most frequent pain category
- Main positive themes

Analyses:
{combined}
"""
    llm_report = _call_llm(synthesis_prompt, "List every finding. Do not skip anything.")
    if not llm_report.strip():
        llm_report = _fallback_analysis(reviews)

    return _add_header(
        llm_report + _build_evidence_section(store, company),
        company, len(reviews), method,
    )


def search_based_analysis(store: ReviewVectorStore, company: str) -> str:
    """Generate analysis using semantic search over indexed reviews."""
    method = _detect_method()
    pain_points = store.search_reviews("complaints problems issues negative bad poor terrible", company=company, n_results=30)
    positives = store.search_reviews("great amazing excellent love wonderful fantastic best", company=company, n_results=30)

    pain_texts = [r["text"] for r in pain_points]
    pos_texts = [r["text"] for r in positives]
    all_reviews = pain_texts + pos_texts

    if not _llm_configured():
        return _add_header(
            _fallback_analysis(all_reviews) + _build_evidence_section(store, company),
            company, len(all_reviews), method,
        )

    pain_section = "\n".join([f"- {t}" for t in pain_texts[:15]])
    pos_section = "\n".join([f"- {t}" for t in pos_texts[:15]])

    prompt = f"""Based on the following semantic search results of customer reviews for "{company}", generate a detailed analysis.

CRITICAL: Only report details that are explicitly visible in the review texts below. If a specific feature or issue is not mentioned, say "not specified in reviews". Never invent specifics.

**Reviews mentioning complaints/issues:**
{pain_section}

**Reviews mentioning praise/positive aspects:**
{pos_section}

Report sections:
1. Main Pain Points
   A. Technical (name specific features/issues only if mentioned in reviews)
   B. UI/UX (name specific screens/buttons only if mentioned)
   C. Customer Support (name specific problems only if mentioned)
2. Most Beloved Things (only from review text)
3. Overall Sentiment
4. Key Statistics (% positive/negative, top pain category, top requests)
"""
    llm_report = _call_llm(prompt, "You are a professional review analyst. Only report facts from the reviews.")
    if not llm_report.strip():
        llm_report = _fallback_analysis(all_reviews)

    evidence_section = _build_evidence_section(store, company)
    return _add_header(llm_report + evidence_section, company, len(pain_texts) + len(pos_texts), method)


def _build_evidence_section(store: ReviewVectorStore, company: str) -> str:
    evidence = _extract_evidence(store, company)
    section = "\n\n---\n## Review Evidence by Category\n"
    for cat_name, cat_key in [("Technical Issues", "technical"), ("UI/UX Issues", "ui_ux"),
                               ("Support Issues", "support"), ("Positive Feedback", "positive")]:
        snippets = evidence.get(cat_key, [])
        if snippets:
            section += f"\n### {cat_name}\n" + "\n".join(f"> {s}" for s in snippets[:5]) + "\n"
        else:
            section += f"\n### {cat_name}\nNo reviews found in this category.\n"
    return section
