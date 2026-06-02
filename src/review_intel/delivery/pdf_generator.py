"""
PDF report generator for the Review Intelligence Platform.

Uses fpdf2 to construct professional, highly structured, evidence-backed
PDF documents from AnalysisResult dictionary payloads.
"""

from __future__ import annotations

import logging
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from fpdf import FPDF

logger = logging.getLogger(__name__)


def _sanitize(text: str) -> str:
    """Clean characters not supported by standard PDF Helvetica font."""
    if not text:
        return ""
    
    replacements = {
        "\u201c": '"', "\u201d": '"',  # smart double quotes
        "\u2018": "'", "\u2019": "'",  # smart single quotes
        "\u2013": "-", "\u2014": "--",  # dashes
        "\u2026": "...",  # ellipsis
        "\u2022": "-",  # bullet
        "\u2192": "->", "\u2190": "<-",  # arrows
        "\u2713": "Yes", "\u2714": "Yes",
        "\u2717": "No", "\u2718": "No",
        "\ufe0f": "",  # variation selector
        "\u2b50": "*",  # star
        "🤖": "[AI]", "🟢": "[Good]", "🔴": "[Critical]", "🟠": "[Warning]", "🟡": "[Info]"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Strip any remaining non-latin1/non-ascii characters to avoid fpdf encoding crash
    text = re.sub(r"[^\x00-\xff]", "", text)
    return text.strip()


class ReviewIntelligencePDF(FPDF):
    """FPDF subclass for formatting review reports."""

    def __init__(self, company_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name = company_name

    def header(self):
        # Header banner on every page except title page
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Review Intelligence Platform - Competitor Analysis: {self.company_name}", 
                      border="B", align="R", new_x="LMARGIN", new_y="NEXT")
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        # Page numbers
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def print_section_heading(self, label: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(26, 54, 93)  # Dark Blue
        self.cell(0, 8, _sanitize(label), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(26, 54, 93)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(4)

    def print_sub_heading(self, label: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(44, 82, 130)  # Slate Blue
        self.cell(0, 6, _sanitize(label), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def print_body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(45, 55, 72)  # Charcoal
        self.multi_cell(0, 5, _sanitize(text))
        self.ln(2)

    def print_blockquote(self, text: str):
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(74, 85, 104)  # Muted Grey
        self.set_fill_color(247, 250, 252)  # Very light grey background
        
        # Left margin spacing for quote
        orig_l_margin = self.l_margin
        self.set_left_margin(orig_l_margin + 5)
        
        sanitized_text = f'"{_sanitize(text)}"'
        self.multi_cell(0, 4.5, sanitized_text, fill=True, border="L")
        
        self.set_left_margin(orig_l_margin)
        self.ln(2)


def generate_report_pdf(result: dict[str, Any]) -> str:
    """
    Generate a highly formatted PDF report from an AnalysisResult dictionary.

    Returns the absolute filepath to the generated PDF.
    """
    company = result.get("company", "Unknown Company")
    
    # Initialize document
    pdf = ReviewIntelligencePDF(company_name=company)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # 1. Document Title / Cover Header
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(26, 54, 93)  # Professional Dark Blue
    pdf.cell(0, 10, f"Customer Intelligence Report", new_x="LMARGIN", new_y="NEXT", align="C")
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(74, 85, 104)
    pdf.cell(0, 8, f"Target: {company}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)

    # Metadata Grid
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(113, 128, 150)
    
    date_val = result.get("analysis_date")
    if hasattr(date_val, "strftime"):
        date_str = date_val.strftime("%Y-%m-%d")
    elif isinstance(date_val, str):
        date_str = date_val[:10]
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    review_count = result.get("review_count", 0)
    sentiment = result.get("overall_sentiment", 0.0)
    
    pdf.cell(60, 5, f"Date: {date_str}", align="C")
    pdf.cell(60, 5, f"Reviews Analyzed: {review_count}", align="C")
    pdf.cell(60, 5, f"Overall Sentiment: {sentiment:+.2f}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Divider line
    pdf.set_draw_color(226, 232, 240)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
    pdf.ln(5)

    # 2. Executive Summary
    if result.get("executive_summary"):
        pdf.print_section_heading("Executive Summary")
        
        # Split markdown formatting gracefully
        summary_text = result["executive_summary"]
        paragraphs = summary_text.split("\n\n")
        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            
            # Simple header extraction for subheadings inside summary
            if p_strip.startswith("## ") or p_strip.startswith("### "):
                clean_sub = p_strip.lstrip("#").strip()
                pdf.print_sub_heading(clean_sub)
            elif p_strip.startswith(">"):
                quote = p_strip.lstrip(">").strip()
                pdf.print_blockquote(quote)
            elif p_strip.startswith("- ") or p_strip.startswith("* "):
                # bullet points
                bullets = p_strip.split("\n")
                for b in bullets:
                    b_clean = b.strip().lstrip("-*").strip()
                    if b_clean:
                        pdf.print_body_text(f" - {b_clean}")
            else:
                pdf.print_body_text(p_strip)

    # 3. Pain Points Section
    if result.get("pain_points"):
        pdf.print_section_heading("Critical Pain Points")
        for i, pp in enumerate(result["pain_points"], 1):
            severity = pp.get("severity", 0)
            status_label = "[CRITICAL]" if severity >= 70 else "[WARNING]" if severity >= 40 else "[INFO]"
            pdf.print_sub_heading(f"{i}. {pp.get('description', '')} {status_label}")
            
            # Details block
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(100, 110, 120)
            pdf.cell(0, 5, f"Severity: {severity}/100 | Frequency: {pp.get('frequency', '?')} mentions | Category: {pp.get('category', '?')}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            
            if pp.get("root_cause_analysis"):
                pdf.print_body_text(f"Root Cause Analysis: {pp['root_cause_analysis']}")
            if pp.get("user_impact"):
                pdf.print_body_text(f"User Impact: {pp['user_impact']}")
            if pp.get("affected_segments"):
                pdf.print_body_text(f"Affected Segments: {pp['affected_segments']}")
                
            quotes = pp.get("evidence_quotes", [])
            if quotes:
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(74, 85, 104)
                pdf.cell(0, 5, "Supporting Evidence:", new_x="LMARGIN", new_y="NEXT")
                for q in quotes[:3]:
                    pdf.print_blockquote(q)
            
            if pp.get("recommended_fix"):
                pdf.print_body_text(f"Recommended Fix: {pp['recommended_fix']}")
            
            pdf.ln(3)

    # 4. Feature Requests Section
    if result.get("feature_requests"):
        pdf.print_section_heading("Feature Opportunities")
        for i, fr in enumerate(result["feature_requests"], 1):
            pdf.print_sub_heading(f"{i}. {fr.get('description', '')} [{fr.get('urgency', 'medium').upper()}]")
            
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(100, 110, 120)
            pdf.cell(0, 5, f"Urgency: {fr.get('urgency', '')} | Frequency: {fr.get('frequency', '?')} mentions", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
            
            if fr.get("use_case"):
                pdf.print_body_text(f"Use Case: {fr['use_case']}")
            if fr.get("current_workaround"):
                pdf.print_body_text(f"Current Workaround: {fr['current_workaround']}")
            if fr.get("competitive_context"):
                pdf.print_body_text(f"Competitive Context: {fr['competitive_context']}")
                
            quotes = fr.get("evidence_quotes", [])
            if quotes:
                for q in quotes[:2]:
                    pdf.print_blockquote(q)
            
            if fr.get("prioritization_rationale"):
                pdf.print_body_text(f"Prioritization Rationale: {fr['prioritization_rationale']}")
            
            pdf.ln(3)

    # 5. Themes Section
    if result.get("themes"):
        pdf.print_section_heading("Thematic Sentiment Analysis")
        for t in result["themes"]:
            sentiment = t.get("sentiment_score", 0)
            sent_str = f"Positive (+{sentiment:.2f})" if sentiment > 0.1 else f"Negative ({sentiment:.2f})" if sentiment < -0.1 else f"Neutral ({sentiment:.2f})"
            pdf.print_sub_heading(f"{t.get('theme', '')} ({sent_str})")
            
            if t.get("analysis"):
                pdf.print_body_text(t["analysis"])
                
            quotes = t.get("key_quotes", [])
            if quotes:
                for q in quotes[:2]:
                    pdf.print_blockquote(q)
                    
            pdf.ln(2)

    # Generate file path
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", company.lower())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.gettempdir())
    filepath = temp_dir / f"review_report_{safe_name}_{timestamp}.pdf"
    
    pdf.output(str(filepath))
    logger.info("Generated PDF report at %s", filepath)
    return str(filepath)
