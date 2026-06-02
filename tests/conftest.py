"""Test configuration and shared fixtures."""

import pytest
from datetime import datetime

from review_intel.schemas.review import Platform, ReviewSchema
from review_intel.schemas.waba import WABATheme


@pytest.fixture
def sample_review() -> ReviewSchema:
    """A single well-formed review for testing."""
    return ReviewSchema(
        text="The broadcast feature is amazing but template approvals take way too long. "
             "We switched from Wati because their pricing was too expensive for our team size. "
             "The chatbot builder needs improvement — it crashes when you add more than 10 nodes.",
        title="Good platform, some issues",
        rating=3.5,
        date=datetime(2025, 6, 15),
        reviewer_name="Priya S.",
        reviewer_role="Marketing Manager",
        company_size="51-200 employees",
        industry="E-commerce",
        country="India",
        verified=True,
        helpful_votes=12,
        platform=Platform.G2,
        competitor_name="Interakt",
        product_category="WhatsApp BSP",
        review_url="https://www.g2.com/products/interakt/reviews/12345",
    )


@pytest.fixture
def sample_reviews() -> list[ReviewSchema]:
    """A batch of diverse reviews for pipeline testing."""
    return [
        ReviewSchema(
            text="Template approval process is frustrating. Takes 3-4 days and often gets rejected without clear reasons.",
            rating=2.0, platform=Platform.G2, competitor_name="Interakt",
            reviewer_role="Growth Lead", verified=True,
        ),
        ReviewSchema(
            text="Love the broadcast campaign feature! Easy to segment audience and track delivery rates.",
            rating=5.0, platform=Platform.CAPTERRA, competitor_name="Interakt",
            reviewer_name="Rahul M.", verified=True,
        ),
        ReviewSchema(
            text="API is unreliable. We've experienced 3 outages in the past month. Webhook callbacks are delayed.",
            rating=1.5, platform=Platform.TRUSTPILOT, competitor_name="Interakt",
            country="India",
        ),
        ReviewSchema(
            text="Switched from AiSensy to Interakt for better Shopify integration. The CRM sync works well.",
            rating=4.0, platform=Platform.G2, competitor_name="Interakt",
            reviewer_role="Founder", company_size="11-50 employees",
        ),
        ReviewSchema(
            text="The shared inbox is decent but lacks proper agent assignment rules. We need better automation.",
            rating=3.0, platform=Platform.CAPTERRA, competitor_name="Interakt",
        ),
        ReviewSchema(
            text="Pricing is very affordable compared to Wati and Gallabox. Best value for Indian SMBs.",
            rating=4.5, platform=Platform.G2, competitor_name="Interakt",
            verified=True,
        ),
        ReviewSchema(
            text="I wish they had WhatsApp Flows support. It would make our lead qualification much easier.",
            rating=3.5, platform=Platform.CAPTERRA, competitor_name="Interakt",
        ),
        ReviewSchema(
            text="Onboarding was smooth. Documentation is clear and support team responded within an hour.",
            rating=5.0, platform=Platform.TRUSTPILOT, competitor_name="Interakt",
            verified=True,
        ),
        ReviewSchema(
            text="The dashboard analytics are basic. No funnel tracking, no revenue attribution. Need better reporting.",
            rating=2.5, platform=Platform.G2, competitor_name="Interakt",
            reviewer_role="Head of Marketing",
        ),
        ReviewSchema(
            text="Great tool for WhatsApp marketing. The CTWA ad integration works seamlessly with Facebook campaigns.",
            rating=4.5, platform=Platform.PRODUCT_HUNT, competitor_name="Interakt",
        ),
    ]


@pytest.fixture
def spam_review() -> ReviewSchema:
    """A clearly spam review."""
    return ReviewSchema(
        text="BEST PRODUCT EVER!!! BUY NOW!!! CLICK HERE https://spam.com AMAZING AMAZING AMAZING!!!",
        platform=Platform.UNKNOWN,
        competitor_name="Interakt",
    )


@pytest.fixture
def duplicate_reviews() -> list[ReviewSchema]:
    """Reviews with exact and near duplicates."""
    return [
        ReviewSchema(
            text="The broadcast feature works great for our marketing campaigns. Easy to use.",
            platform=Platform.G2, competitor_name="Interakt",
        ),
        ReviewSchema(
            text="The broadcast feature works great for our marketing campaigns. Easy to use.",
            platform=Platform.CAPTERRA, competitor_name="Interakt",
        ),
        ReviewSchema(
            text="The broadcast feature works great for marketing campaigns. Very easy to use.",
            platform=Platform.TRUSTPILOT, competitor_name="Interakt",
        ),
        ReviewSchema(
            text="Completely different review about API reliability and webhook issues.",
            platform=Platform.G2, competitor_name="Interakt",
        ),
    ]
