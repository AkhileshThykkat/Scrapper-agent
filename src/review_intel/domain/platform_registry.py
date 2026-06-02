"""
Platform registry — metadata for all target WABA/SaaS platforms.

Used to map competitor names to platform categories, configure
collection strategies, and provide context to the analysis chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from review_intel.schemas.waba import CompetitorCategory


@dataclass(frozen=True)
class PlatformInfo:
    """Metadata about a target platform."""
    name: str
    slug: str
    category: CompetitorCategory
    primary_market: str = ""
    key_differentiator: str = ""
    g2_slug: str = ""
    capterra_slug: str = ""
    trustpilot_domain: str = ""
    product_hunt_slug: str = ""
    website: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)


# ─── Target Platform Registry ────────────────────────────────────────────────

PLATFORMS: dict[str, PlatformInfo] = {
    "interakt": PlatformInfo(
        name="Interakt",
        slug="interakt",
        category=CompetitorCategory.BSP,
        primary_market="India SMB",
        key_differentiator="Shopify integration, affordable pricing",
        g2_slug="interakt",
        capterra_slug="interakt",
        trustpilot_domain="interakt.shop",
        website="https://www.interakt.shop",
        aliases=("interakt.shop", "haptik interakt"),
    ),
    "wati": PlatformInfo(
        name="Wati",
        slug="wati",
        category=CompetitorCategory.BSP,
        primary_market="Global SMB/Mid",
        key_differentiator="Easy setup, team inbox",
        g2_slug="wati-io",
        capterra_slug="wati",
        trustpilot_domain="wati.io",
        website="https://www.wati.io",
        aliases=("wati.io", "wati whatsapp"),
    ),
    "aisensy": PlatformInfo(
        name="AiSensy",
        slug="aisensy",
        category=CompetitorCategory.BSP,
        primary_market="India SMB",
        key_differentiator="Broadcast focus, affordable",
        g2_slug="aisensy",
        capterra_slug="aisensy",
        trustpilot_domain="aisensy.com",
        website="https://www.aisensy.com",
        aliases=("aisensy.com",),
    ),
    "gallabox": PlatformInfo(
        name="Gallabox",
        slug="gallabox",
        category=CompetitorCategory.BSP,
        primary_market="India SMB",
        key_differentiator="Commerce features, shared inbox",
        g2_slug="gallabox",
        capterra_slug="gallabox",
        trustpilot_domain="gallabox.com",
        website="https://www.gallabox.com",
        aliases=("gallabox.com",),
    ),
    "doubletick": PlatformInfo(
        name="DoubleTick",
        slug="doubletick",
        category=CompetitorCategory.BSP,
        primary_market="India SMB",
        key_differentiator="Green tick, sales CRM",
        g2_slug="doubletick",
        capterra_slug="doubletick",
        trustpilot_domain="doubletick.io",
        website="https://www.doubletick.io",
        aliases=("doubletick.io", "double tick"),
    ),
    "gupshup": PlatformInfo(
        name="Gupshup",
        slug="gupshup",
        category=CompetitorCategory.CPAAS,
        primary_market="Enterprise",
        key_differentiator="Multi-channel, conversation AI",
        g2_slug="gupshup",
        capterra_slug="gupshup",
        trustpilot_domain="gupshup.io",
        website="https://www.gupshup.io",
        aliases=("gupshup.io",),
    ),
    "respond_io": PlatformInfo(
        name="Respond.io",
        slug="respond-io",
        category=CompetitorCategory.OMNICHANNEL,
        primary_market="Global Mid/Enterprise",
        key_differentiator="Multi-channel inbox",
        g2_slug="respond-io",
        capterra_slug="respond-io",
        trustpilot_domain="respond.io",
        website="https://respond.io",
        aliases=("respond.io", "respondio"),
    ),
    "sleekflow": PlatformInfo(
        name="SleekFlow",
        slug="sleekflow",
        category=CompetitorCategory.OMNICHANNEL,
        primary_market="APAC",
        key_differentiator="Social selling, commerce",
        g2_slug="sleekflow",
        capterra_slug="sleekflow",
        trustpilot_domain="sleekflow.io",
        website="https://sleekflow.io",
        aliases=("sleekflow.io",),
    ),
    "messagebird": PlatformInfo(
        name="MessageBird",
        slug="messagebird",
        category=CompetitorCategory.CPAAS,
        primary_market="Global Enterprise",
        key_differentiator="Omnichannel, APIs",
        g2_slug="messagebird",
        capterra_slug="messagebird",
        trustpilot_domain="messagebird.com",
        website="https://www.messagebird.com",
        aliases=("messagebird.com", "bird.com", "bird"),
    ),
    "twilio": PlatformInfo(
        name="Twilio",
        slug="twilio",
        category=CompetitorCategory.CPAAS,
        primary_market="Global Enterprise",
        key_differentiator="Developer-first, APIs",
        g2_slug="twilio",
        capterra_slug="twilio",
        trustpilot_domain="twilio.com",
        website="https://www.twilio.com",
        aliases=("twilio.com",),
    ),
    "freshchat": PlatformInfo(
        name="Freshchat",
        slug="freshchat",
        category=CompetitorCategory.SUPPORT,
        primary_market="Global Mid/Enterprise",
        key_differentiator="Native WhatsApp channel, Freshworks suite",
        g2_slug="freshchat",
        capterra_slug="freshchat",
        trustpilot_domain="freshworks.com",
        website="https://www.freshworks.com/freshchat/",
        aliases=("freshworks freshchat",),
    ),
    "hubspot": PlatformInfo(
        name="HubSpot",
        slug="hubspot",
        category=CompetitorCategory.CRM,
        primary_market="Global",
        key_differentiator="All-in-one CRM",
        g2_slug="hubspot",
        capterra_slug="hubspot-crm",
        trustpilot_domain="hubspot.com",
        website="https://www.hubspot.com",
        aliases=("hubspot.com",),
    ),
    "zendesk": PlatformInfo(
        name="Zendesk",
        slug="zendesk",
        category=CompetitorCategory.SUPPORT,
        primary_market="Global Enterprise",
        key_differentiator="Ticketing, support suite",
        g2_slug="zendesk-support-suite",
        capterra_slug="zendesk",
        trustpilot_domain="zendesk.com",
        website="https://www.zendesk.com",
        aliases=("zendesk.com",),
    ),
    "salesforce": PlatformInfo(
        name="Salesforce",
        slug="salesforce",
        category=CompetitorCategory.CRM,
        primary_market="Global Enterprise",
        key_differentiator="Enterprise CRM, ecosystem",
        g2_slug="salesforce-crm",
        capterra_slug="salesforce-crm",
        trustpilot_domain="salesforce.com",
        website="https://www.salesforce.com",
        aliases=("salesforce.com", "sfdc"),
    ),
    "meta_whatsapp": PlatformInfo(
        name="Meta WhatsApp Business Platform",
        slug="meta-whatsapp-business",
        category=CompetitorCategory.PLATFORM,
        primary_market="Global",
        key_differentiator="Direct Cloud API / On-Premise API",
        g2_slug="whatsapp-business-platform",
        website="https://business.whatsapp.com",
        aliases=("whatsapp business", "whatsapp api", "meta business platform"),
    ),
}


def get_platform(name: str) -> PlatformInfo | None:
    """Look up a platform by name, slug, or alias (case-insensitive)."""
    name_lower = name.lower().strip()

    # Direct match
    if name_lower in PLATFORMS:
        return PLATFORMS[name_lower]

    # Slug match
    for info in PLATFORMS.values():
        if info.slug == name_lower:
            return info

    # Alias match
    for info in PLATFORMS.values():
        if name_lower in (a.lower() for a in info.aliases):
            return info
        if name_lower == info.name.lower():
            return info

    return None


def get_all_platforms() -> list[PlatformInfo]:
    """Return all registered platforms."""
    return list(PLATFORMS.values())


def get_platforms_by_category(category: CompetitorCategory) -> list[PlatformInfo]:
    """Return all platforms in a given category."""
    return [p for p in PLATFORMS.values() if p.category == category]
