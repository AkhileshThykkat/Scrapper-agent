import io
import re
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

UNICODE_FONT_DIR = Path(__file__).parent / "fonts"

BOLD_MARKER = "##B##"
END_BOLD_MARKER = "##EB##"


def _sanitize(text: str) -> str:
    """Remove or replace characters that can't render in standard PDF fonts."""
    replacements = {
        "\u201c": '"', "\u201d": '"',  # smart double quotes
        "\u2018": "'", "\u2019": "'",  # smart single quotes
        "\u2013": "-", "\u2014": "--",  # dashes
        "\u2026": "...",  # ellipsis
        "\u2022": "-",  # bullet
        "\u2192": "->", "\u2190": "<-",  # arrows
        "\u2713": "✓", "\u2714": "✓",
        "\u2717": "✗", "\u2718": "✗",
        "\ufe0f": "",  # variation selector
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^\x00-\x7F]", "", text)
    return text.strip()


def _parse_markdown_line(line: str):
    """Parse a markdown line and return (text, is_bold, level) where level is 0=normal, 1=h1, 2=h2, 3=h3."""
    stripped = line.strip()
    if not stripped:
        return "", 0, 0
    if stripped.startswith("# "):
        return _sanitize(stripped[2:]), 0, 1
    if stripped.startswith("## "):
        return _sanitize(stripped[3:]), 0, 2
    if stripped.startswith("### "):
        return _sanitize(stripped[4:]), 0, 3
    if stripped.startswith("**") and stripped.endswith("**"):
        return _sanitize(stripped[2:-2]), 1, 0
    if stripped.startswith("- ") or stripped.startswith("* "):
        return "  " + _sanitize(stripped[2:]), 0, 0
    return _sanitize(stripped), 0, 0


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "Review Analysis Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def safe_multi_cell(self, w: float, h: float, text: str, **kwargs):
        try:
            self.multi_cell(w, h, text, **kwargs)
        except Exception:
            try:
                ascii_only = text.encode("ascii", errors="replace").decode("ascii")
                self.multi_cell(w, h, ascii_only, **kwargs)
            except Exception:
                pass


def generate_report_pdf(company: str, report: str, review_count: int, analysis_timestamp: str) -> bytes:
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Company: {_sanitize(company)}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Analysis Date: {analysis_timestamp}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Reviews Analyzed: {review_count}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for line in report.split("\n"):
        text, is_bold, level = _parse_markdown_line(line)
        if not text:
            pdf.ln(2)
            continue

        if level == 1:
            pdf.set_font("Helvetica", "B", 13)
            pdf.ln(2)
            pdf.safe_multi_cell(0, 7, text)
            pdf.set_font("Helvetica", "", 10)
        elif level == 2:
            pdf.set_font("Helvetica", "B", 11)
            pdf.ln(1)
            pdf.safe_multi_cell(0, 6, text)
            pdf.set_font("Helvetica", "", 10)
        elif level == 3:
            pdf.set_font("Helvetica", "B", 10)
            pdf.safe_multi_cell(0, 6, text)
            pdf.set_font("Helvetica", "", 10)
        elif is_bold:
            pdf.set_font("Helvetica", "B", 10)
            pdf.safe_multi_cell(0, 5, text)
            pdf.set_font("Helvetica", "", 10)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.safe_multi_cell(0, 5, text)

    return bytes(pdf.output())
