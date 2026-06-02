"""Unit tests for the PDF report generator."""

import os
from datetime import datetime

from review_intel.delivery.pdf_generator import generate_report_pdf


def test_pdf_generation():
    """Verify that PDF generation completes successfully with a sample payload."""
    sample_result = {
        "company": "Test Company",
        "analysis_date": datetime.now().isoformat(),
        "review_count": 42,
        "overall_sentiment": 0.45,
        "executive_summary": (
            "## Summary\nThis is a sample executive summary narrative.\n\n"
            "> \"Direct quote from user review goes here\"\n\n"
            "And a concluding thought."
        ),
        "pain_points": [
            {
                "description": "Template approval delays",
                "severity": 85,
                "frequency": 14,
                "category": "workflow",
                "root_cause_analysis": "Delay on Meta side combined with slow local BSP processing.",
                "user_impact": "Blocks instant campaigns.",
                "affected_segments": "Enterprise users",
                "evidence_quotes": [
                    "Template approvals take way too long, sometimes 3-4 business days.",
                ],
                "recommended_fix": "Implement local pre-validation checks."
            }
        ],
        "feature_requests": [
            {
                "description": "WhatsApp Flows support",
                "urgency": "high",
                "frequency": 9,
                "use_case": "Interactive lead forms.",
                "current_workaround": "Send external Google Forms links.",
                "competitive_context": "Wati offers native Flows.",
                "evidence_quotes": [
                    "We need Flows to optimize onboarding templates."
                ],
                "prioritization_rationale": "High competitive pressure."
            }
        ],
        "themes": [
            {
                "theme": "pricing",
                "sentiment_score": -0.4,
                "frequency": 10,
                "severity_score": 60,
                "trend_direction": "declining",
                "analysis": "Many users find the new message-based pricing model expensive.",
                "key_quotes": ["Pricing is too high for our volume."]
            }
        ],
        "pipeline_metadata": {
            "waba_themes": {
                "pricing": 10,
                "templates": 14
            }
        }
    }

    pdf_path = generate_report_pdf(sample_result)
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) > 0
    # Clean up
    os.remove(pdf_path)
