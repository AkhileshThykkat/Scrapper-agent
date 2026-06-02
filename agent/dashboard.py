"""Renders the review analysis report as a structured HTML dashboard."""

import re
from datetime import datetime


def _parse_sections(report: str) -> dict:
    """Parse markdown report into structured sections."""
    sections = {
        "pain_points": {"technical": [], "ui_ux": [], "support": []},
        "beloved": [],
        "sentiment": "",
        "statistics": [],
        "evidence": {"technical": [], "ui_ux": [], "support": [], "positive": []},
        "misclassified": [],
    }

    current_main = None
    current_sub = None
    in_evidence = False

    for line in report.split("\n"):
        stripped = line.strip()

        if stripped.startswith("## Review Evidence by Category"):
            in_evidence = True
            continue
        if stripped.startswith("## Potentially Misclassified Evidence"):
            current_main = "misclassified"
            in_evidence = False
            continue

        if in_evidence:
            if stripped.startswith("### "):
                label = stripped[4:].lower()
                if "technical" in label:
                    current_sub = "technical"
                elif "ui" in label or "ux" in label:
                    current_sub = "ui_ux"
                elif "support" in label:
                    current_sub = "support"
                elif "positive" in label or "beloved" in label:
                    current_sub = "positive"
                else:
                    current_sub = None
            elif stripped.startswith("> ") and current_sub:
                sections["evidence"][current_sub].append(stripped[2:])
            elif current_sub == "positive" and not stripped.startswith(">") and stripped and not stripped.startswith("No reviews"):
                pass
            continue

        if stripped.startswith("### A.") or stripped.startswith("### Technical"):
            current_main = "pain_points"
            current_sub = "technical"
            continue
        if stripped.startswith("### B.") or stripped.startswith("### UI/UX"):
            current_main = "pain_points"
            current_sub = "ui_ux"
            continue
        if stripped.startswith("### C.") or stripped.startswith("### Customer Support"):
            current_main = "pain_points"
            current_sub = "support"
            continue
        if stripped.startswith("## 1.") or stripped.startswith("## Main Pain Points"):
            current_main = "pain_points"
            current_sub = None
            continue
        if stripped.startswith("## 2.") or stripped.startswith("## Most Beloved"):
            current_main = "beloved"
            current_sub = None
            continue
        if stripped.startswith("## 3.") or stripped.startswith("## Overall Sentiment"):
            current_main = "sentiment"
            current_sub = None
            continue
        if stripped.startswith("## 4.") or stripped.startswith("## Key Statistics"):
            current_main = "statistics"
            current_sub = None
            continue

        if current_main == "pain_points" and current_sub and stripped.startswith("- "):
            sections["pain_points"][current_sub].append(stripped[2:])
        elif current_main == "pain_points" and current_sub and stripped and not stripped.startswith("#"):
            text = re.sub(r"^\*\*.*?\*\*\s*", "", stripped)
            if text and not text.startswith("List") and not text.startswith("For each"):
                sections["pain_points"][current_sub].append(text)
        elif current_main == "beloved" and stripped.startswith("- "):
            sections["beloved"].append(stripped[2:])
        elif current_main == "beloved" and stripped and not stripped.startswith("#") and not stripped.startswith("List"):
            sections["beloved"].append(stripped)
        elif current_main == "sentiment" and stripped and not stripped.startswith("#"):
            sections["sentiment"] += " " + stripped
        elif current_main == "statistics" and stripped and not stripped.startswith("#"):
            sections["statistics"].append(stripped)
        elif current_main == "misclassified" and stripped.startswith("> "):
            sections["misclassified"].append(stripped[2:])

    return sections


def _css() -> str:
    return """
<style>
.dashboard { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; }
.dashboard h1 { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
.dashboard h2 { font-size: 18px; font-weight: 600; margin: 24px 0 12px; padding-bottom: 6px; border-bottom: 2px solid var(--border-color-primary, #e8e8f0); }
.dashboard h3 { font-size: 15px; font-weight: 600; margin: 16px 0 6px; }
.meta-bar { display: flex; gap: 12px; flex-wrap: wrap; margin: 12px 0 20px; }
.meta-chip { background: var(--background-fill-secondary, #f0f2f5); border-radius: 20px; padding: 4px 14px; font-size: 13px; color: var(--body-text-color); }
.meta-chip strong { color: var(--body-text-color); }
.badge { display: inline-block; border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: 500; margin-right: 6px; }
.badge-tech { background: #e8f4fd; color: #1a6fb5; }
.badge-ui { background: #f0e6ff; color: #7c3aed; }
.badge-support { background: #fff3e0; color: #e65100; }
.badge-positive { background: #e8f5e9; color: #2e7d32; }
.badge-neutral { background: var(--background-fill-secondary, #f5f5f5); color: var(--body-text-color); }
.card { background: var(--background-fill-primary, #fff); border: 1px solid var(--border-color-primary, #e8e8f0); border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.card-title { font-weight: 600; font-size: 14px; }
.count-badge { background: var(--background-fill-secondary, #f0f2f5); border-radius: 10px; padding: 1px 8px; font-size: 12px; color: var(--body-text-color); }
.evidence-item { padding: 8px 12px; margin: 4px 0; background: var(--background-fill-secondary, #f8f9fb); border-left: 3px solid var(--border-color-primary, #d0d5dd); border-radius: 0 6px 6px 0; font-size: 13px; line-height: 1.5; color: var(--body-text-color); }
.evidence-item.tech { border-left-color: #1a6fb5; }
.evidence-item.ui { border-left-color: #7c3aed; }
.evidence-item.support { border-left-color: #e65100; }
.evidence-item.positive { border-left-color: #2e7d32; }
.evidence-group { margin: 8px 0; }
.evidence-group summary { cursor: pointer; font-weight: 500; font-size: 13px; padding: 4px 0; color: var(--body-text-color); }
.evidence-group summary:hover { opacity: 0.8; }
.summary-text { font-size: 14px; line-height: 1.6; margin: 8px 0; color: var(--body-text-color); }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; margin: 10px 0; }
.stat-card { background: var(--background-fill-secondary, #f8f9fb); border-radius: 8px; padding: 12px; text-align: center; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--body-text-color); }
.stat-label { font-size: 12px; margin-top: 2px; color: var(--body-text-color); }
.empty-state { font-style: italic; font-size: 13px; padding: 8px; color: var(--body-text-color); opacity: 0.7; }
.note-box { background: rgba(255, 235, 59, 0.1); border: 1px solid rgba(255, 235, 59, 0.3); border-radius: 8px; padding: 12px; font-size: 13px; margin: 12px 0; }
</style>"""


def render_dashboard(report: str, company: str, review_count: int, method: str) -> str:
    """Convert the analysis report into a structured HTML dashboard."""
    sections = _parse_sections(report)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = _css()
    html += '<div class="dashboard">'

    # ── Header ──
    html += f"<h1>{company}</h1>"
    html += '<div class="meta-bar">'
    html += f'<span class="meta-chip"><strong>Date:</strong> {timestamp}</span>'
    html += f'<span class="meta-chip"><strong>Reviews:</strong> {review_count}</span>'
    html += f'<span class="meta-chip"><strong>Method:</strong> {method}</span>'
    html += "</div>"

    # ── Executive Summary ──
    html += "<h2>Executive Summary</h2>"
    pain_count = sum(len(v) for v in sections["pain_points"].values())
    beloved_count = len(sections["beloved"])
    top_cat = max(sections["pain_points"], key=lambda k: len(sections["pain_points"][k])) if pain_count > 0 else ""
    top_cat_label = {"technical": "Technical", "ui_ux": "UI/UX", "support": "Customer Support"}.get(top_cat, "N/A")

    html += '<div class="stat-grid">'
    html += f'<div class="stat-card"><div class="stat-value">{review_count}</div><div class="stat-label">Reviews Analyzed</div></div>'
    html += f'<div class="stat-card"><div class="stat-value">{pain_count}</div><div class="stat-label">Pain Points Identified</div></div>'
    html += f'<div class="stat-card"><div class="stat-value">{beloved_count}</div><div class="stat-label">Positive Themes</div></div>'
    html += f'<div class="stat-card"><div class="stat-value">{top_cat_label}</div><div class="stat-label">Top Pain Category</div></div>'
    html += "</div>"

    if sections["sentiment"]:
        html += f'<div class="card"><div class="card-title">Overall Sentiment</div><div class="summary-text">{sections["sentiment"].strip()}</div></div>'

    # ── Pain Points ──
    html += "<h2>Pain Points</h2>"
    cat_config = [
        ("technical", "Technical Issues", "badge-tech"),
        ("ui_ux", "UI/UX Issues", "badge-ui"),
        ("support", "Customer Support Issues", "badge-support"),
    ]
    for key, label, badge_class in cat_config:
        items = sections["pain_points"].get(key, [])
        evidence = sections["evidence"].get(key, [])
        html += '<div class="card">'
        html += f'<div class="card-header"><span class="card-title"><span class="badge {badge_class}">{label}</span></span><span class="count-badge">{len(items)} findings</span></div>'
        if items:
            for item in items:
                html += f'<div class="evidence-item {key.split("_")[0]}">{item}</div>'
        else:
            html += '<div class="empty-state">No specific points identified in this category.</div>'
        if evidence:
            html += f'<div class="evidence-group"><details><summary>View {len(evidence)} supporting review excerpts</summary>'
            for e in evidence[:5]:
                html += f'<div class="evidence-item {key.split("_")[0]}">{e}</div>'
            html += "</details></div>"
        html += "</div>"

    # ── Positive Feedback ──
    html += "<h2>Positive Feedback</h2>"
    html += '<div class="card">'
    html += f'<div class="card-header"><span class="card-title"><span class="badge badge-positive">Most Beloved Things</span></span><span class="count-badge">{len(sections["beloved"])} themes</span></div>'
    if sections["beloved"]:
        for item in sections["beloved"]:
            html += f'<div class="evidence-item positive">{item}</div>'
    else:
        html += '<div class="empty-state">No positive themes identified.</div>'
    pos_evidence = sections["evidence"].get("positive", [])
    if pos_evidence:
        html += f'<div class="evidence-group"><details><summary>View {len(pos_evidence)} supporting review excerpts</summary>'
        for e in pos_evidence[:5]:
            html += f'<div class="evidence-item positive">{e}</div>'
        html += "</details></div>"
    html += "</div>"

    # ── Key Statistics ──
    if sections["statistics"]:
        html += "<h2>Key Statistics</h2>"
        html += '<div class="card">'
        for stat in sections["statistics"]:
            clean = stat.lstrip("- ").strip("*")
            html += f'<div class="summary-text">• {clean}</div>'
        html += "</div>"

    # ── Misclassified Evidence ──
    if sections["misclassified"]:
        html += "<h2>Potentially Misclassified Evidence</h2>"
        html += '<div class="card">'
        for item in sections["misclassified"]:
            html += f'<div class="evidence-item">{item}</div>'
        html += "</div>"

    # ── Data Quality Notes ──
    html += "<h2>Data Quality Notes</h2>"
    html += '<div class="note-box">'
    notes = []
    if review_count < 30:
        notes.append(f"Small sample size ({review_count} reviews). Findings may not be representative.")
    if "keyword" in method.lower():
        notes.append("Analysis is keyword-based (no LLM configured). Themes are inferred from keyword frequency.")
    if not notes:
        notes.append("No data quality issues detected.")
    for n in notes:
        html += f"<div>• {n}</div>"
    html += "</div>"

    html += "</div>"
    return html
