"""
WABA (WhatsApp Business API) specific enums and theme definitions.

These themes are used for automatic review classification and
domain-aware LLM prompting.
"""

from __future__ import annotations

from enum import Enum


class WABATheme(str, Enum):
    """
    WABA-specific themes detected in customer reviews.

    Each theme maps to a set of keywords in the domain taxonomy
    and is used by the classifier and analysis chain.
    """
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


class WhatsAppConcept(str, Enum):
    """
    WhatsApp ecosystem-level concepts that may appear in reviews,
    changelogs, or community discussions.
    """
    CLOUD_API = "cloud_api"
    ON_PREMISE_API = "on_premise_api"
    EMBEDDED_SIGNUP = "embedded_signup"
    BUSINESS_VERIFICATION = "business_verification"
    CTWA_ADS = "ctwa_ads"
    TEMPLATE_CATEGORIES = "template_categories"
    CONVERSATION_CATEGORIES = "conversation_categories"
    AUTH_TEMPLATES = "auth_templates"
    UTILITY_TEMPLATES = "utility_templates"
    MARKETING_TEMPLATES = "marketing_templates"
    FLOW_MESSAGES = "flow_messages"
    WHATSAPP_FLOWS = "whatsapp_flows"
    COMMERCE_MESSAGING = "commerce_messaging"
    WEBHOOK_CONFIG = "webhook_config"
    PHONE_NUMBER_MIGRATION = "phone_number_migration"
    QUALITY_RATING = "quality_rating"
    MESSAGING_LIMITS = "messaging_limits"
    GREEN_TICK = "green_tick"
    INTERACTIVE_MESSAGES = "interactive_messages"
    PER_CONVERSATION_PRICING = "per_conversation_pricing"


class CompetitorCategory(str, Enum):
    """Categories of WABA ecosystem competitors."""
    BSP = "bsp"                      # Business Solution Provider
    CPAAS = "cpaas"                  # Communications Platform as a Service
    CRM = "crm"                      # CRM with WhatsApp integration
    SUPPORT = "support"              # Support platform with WhatsApp channel
    PLATFORM = "platform"            # Meta's own platform
    OMNICHANNEL = "omnichannel"      # Multi-channel engagement platforms
