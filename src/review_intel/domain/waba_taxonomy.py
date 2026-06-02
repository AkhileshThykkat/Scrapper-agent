"""
WABA concept taxonomy and keyword maps.

This module encodes domain knowledge about the WhatsApp Business ecosystem.
It is used by the classifier to tag reviews and by the analysis chain
to inject domain context into LLM prompts.
"""

from __future__ import annotations

from review_intel.schemas.waba import WABATheme, WhatsAppConcept


# ─── Theme → Keyword Map ─────────────────────────────────────────────────────
# Each theme maps to keywords/phrases that indicate the theme is being discussed.
# Used by the rule-based classifier as a first pass before LLM classification.

THEME_KEYWORDS: dict[WABATheme, list[str]] = {
    WABATheme.BROADCAST_CAMPAIGNS: [
        "broadcast", "bulk message", "mass message", "campaign",
        "bulk send", "promotional message", "marketing message",
        "newsletter", "announcement", "blast", "bulk messaging",
        "campaign manager", "broadcast list", "send to all",
    ],
    WABATheme.TEMPLATE_MANAGEMENT: [
        "template", "message template", "pre-approved",
        "template format", "template variable", "dynamic content",
        "header template", "media template", "template builder",
        "template library", "template editor",
    ],
    WABATheme.TEMPLATE_APPROVALS: [
        "template approval", "template reject", "pending approval",
        "meta approval", "template review", "approval process",
        "template status", "rejected template", "appeal",
        "approval delay", "template pending", "not approved",
    ],
    WABATheme.CTWA_WORKFLOWS: [
        "click to whatsapp", "ctwa", "whatsapp ad", "facebook ad",
        "instagram ad", "ad click", "click-to-chat",
        "ad integration", "lead from ad", "click to chat",
        "ad campaign", "meta ad",
    ],
    WABATheme.SHARED_INBOX: [
        "shared inbox", "team inbox", "multi-agent",
        "agent assignment", "conversation routing", "queue",
        "team collaboration", "assign conversation", "inbox",
        "team chat", "agent inbox", "collaborative inbox",
    ],
    WABATheme.CHATBOT_BUILDER: [
        "chatbot", "bot builder", "no-code bot", "auto reply",
        "automated response", "conversation bot", "ai bot",
        "chat automation", "bot flow", "bot template",
        "chatbot builder", "bot design", "virtual assistant",
    ],
    WABATheme.FLOW_BUILDER: [
        "flow builder", "workflow", "automation flow",
        "whatsapp flow", "interactive flow", "form flow",
        "multi-step", "conversation flow", "flow editor",
        "visual flow", "drag and drop flow",
    ],
    WABATheme.INTEGRATIONS: [
        "integration", "connect", "sync", "api",
        "zapier", "shopify", "woocommerce",
        "hubspot", "salesforce", "zoho", "pipedrive",
        "third party", "third-party", "plugin", "addon",
        "google sheets", "make.com", "pabbly",
    ],
    WABATheme.CRM_SYNC: [
        "crm", "contact sync", "lead management",
        "deal tracking", "pipeline", "contact management",
        "customer data", "contact import", "lead capture",
        "contact list", "customer database",
    ],
    WABATheme.CATALOG_SUPPORT: [
        "catalog", "product catalog", "product message",
        "product list", "shopping", "ecommerce",
        "product display", "multi-product", "single product",
        "product card",
    ],
    WABATheme.COMMERCE: [
        "commerce", "order", "payment", "cart",
        "checkout", "purchase", "buy", "sell",
        "transaction", "invoice", "cod", "cash on delivery",
        "order tracking", "order management",
    ],
    WABATheme.AUTOMATION: [
        "automation", "automate", "auto", "trigger",
        "rule", "workflow", "scheduled", "automatic",
        "smart", "intelligent routing", "auto-assign",
        "auto-reply", "drip campaign", "sequence",
    ],
    WABATheme.WEBHOOKS: [
        "webhook", "callback", "event notification",
        "real-time update", "push notification",
        "api callback", "event hook", "webhook url",
        "webhook endpoint",
    ],
    WABATheme.API_RELIABILITY: [
        "api", "uptime", "downtime", "outage",
        "server error", "500 error", "timeout",
        "rate limit", "api speed", "latency",
        "reliability", "stability", "api issue",
        "api down", "service disruption", "message delay",
        "message not delivered", "delivery failure",
    ],
    WABATheme.MULTI_AGENT: [
        "multi-agent", "multiple agent", "team member",
        "agent seat", "user seat", "team size",
        "concurrent agent", "agent limit", "user limit",
        "team plan", "per agent pricing",
    ],
    WABATheme.REPORTING: [
        "report", "analytics", "dashboard", "metrics",
        "statistics", "insight", "data", "chart",
        "graph", "export", "download report", "kpi",
        "conversion rate", "response time report",
    ],
    WABATheme.PRICING: [
        "price", "pricing", "cost", "expensive",
        "affordable", "cheap", "plan", "subscription",
        "billing", "invoice", "charge", "fee",
        "free trial", "discount", "value for money",
        "overpriced", "hidden charge", "per conversation",
        "markup", "pricing model",
    ],
    WABATheme.ONBOARDING: [
        "onboarding", "setup", "getting started",
        "documentation", "tutorial", "guide",
        "learning curve", "easy to set up",
        "difficult to set up", "configuration",
        "initial setup", "first time", "migration",
        "account setup", "number verification",
    ],
}


# ─── WhatsApp Ecosystem Concept Keywords ──────────────────────────────────────

CONCEPT_KEYWORDS: dict[WhatsAppConcept, list[str]] = {
    WhatsAppConcept.CLOUD_API: [
        "cloud api", "whatsapp cloud", "cloud-hosted api",
        "meta cloud api",
    ],
    WhatsAppConcept.ON_PREMISE_API: [
        "on-premise", "on premise", "self-hosted", "on-prem api",
    ],
    WhatsAppConcept.EMBEDDED_SIGNUP: [
        "embedded signup", "facebook login", "meta login",
        "quick signup", "one-click signup",
    ],
    WhatsAppConcept.BUSINESS_VERIFICATION: [
        "business verification", "verify business",
        "meta verification", "facebook verification",
        "business manager verification",
    ],
    WhatsAppConcept.CTWA_ADS: [
        "click to whatsapp ad", "ctwa ad", "whatsapp ad",
        "click-to-whatsapp", "conversation ad",
    ],
    WhatsAppConcept.TEMPLATE_CATEGORIES: [
        "template category", "authentication template",
        "utility template", "marketing template",
        "template type",
    ],
    WhatsAppConcept.CONVERSATION_CATEGORIES: [
        "conversation category", "service conversation",
        "marketing conversation", "utility conversation",
        "authentication conversation", "conversation type",
        "conversation-based pricing",
    ],
    WhatsAppConcept.AUTH_TEMPLATES: [
        "otp template", "authentication template", "otp message",
        "verification code", "login otp",
    ],
    WhatsAppConcept.UTILITY_TEMPLATES: [
        "utility template", "order update", "shipping notification",
        "booking confirmation", "transactional message",
    ],
    WhatsAppConcept.MARKETING_TEMPLATES: [
        "marketing template", "promotional template",
        "offer message", "discount message",
    ],
    WhatsAppConcept.FLOW_MESSAGES: [
        "flow message", "interactive form", "in-chat form",
    ],
    WhatsAppConcept.WHATSAPP_FLOWS: [
        "whatsapp flow", "wa flow", "flow feature",
        "flow builder whatsapp",
    ],
    WhatsAppConcept.COMMERCE_MESSAGING: [
        "commerce message", "product message", "catalog message",
        "order message", "payment message",
    ],
    WhatsAppConcept.WEBHOOK_CONFIG: [
        "webhook configuration", "webhook setup",
        "webhook url", "webhook endpoint",
    ],
    WhatsAppConcept.PHONE_NUMBER_MIGRATION: [
        "number migration", "phone migration", "port number",
        "transfer number", "migrate number", "change bsp",
        "switch provider",
    ],
    WhatsAppConcept.QUALITY_RATING: [
        "quality rating", "quality score", "green quality",
        "yellow quality", "red quality", "flagged number",
    ],
    WhatsAppConcept.MESSAGING_LIMITS: [
        "messaging limit", "message limit", "tier 1", "tier 2",
        "tier 3", "sending limit", "daily limit",
        "1000 message limit",
    ],
    WhatsAppConcept.GREEN_TICK: [
        "green tick", "verified badge", "official business",
        "blue tick", "verified account", "oba",
    ],
    WhatsAppConcept.INTERACTIVE_MESSAGES: [
        "interactive message", "quick reply", "list message",
        "button message", "cta button", "reply button",
    ],
    WhatsAppConcept.PER_CONVERSATION_PRICING: [
        "per conversation", "conversation pricing",
        "conversation charge", "conversation cost",
        "per chat pricing",
    ],
}


# ─── Concept Category Groupings ──────────────────────────────────────────────

CONCEPT_CATEGORIES: dict[str, list[WhatsAppConcept]] = {
    "messaging": [
        WhatsAppConcept.CLOUD_API,
        WhatsAppConcept.ON_PREMISE_API,
        WhatsAppConcept.CONVERSATION_CATEGORIES,
        WhatsAppConcept.MESSAGING_LIMITS,
        WhatsAppConcept.PER_CONVERSATION_PRICING,
        WhatsAppConcept.INTERACTIVE_MESSAGES,
    ],
    "templates": [
        WhatsAppConcept.TEMPLATE_CATEGORIES,
        WhatsAppConcept.AUTH_TEMPLATES,
        WhatsAppConcept.UTILITY_TEMPLATES,
        WhatsAppConcept.MARKETING_TEMPLATES,
    ],
    "commerce": [
        WhatsAppConcept.COMMERCE_MESSAGING,
        WhatsAppConcept.FLOW_MESSAGES,
        WhatsAppConcept.WHATSAPP_FLOWS,
    ],
    "engagement": [
        WhatsAppConcept.CTWA_ADS,
    ],
    "platform": [
        WhatsAppConcept.EMBEDDED_SIGNUP,
        WhatsAppConcept.BUSINESS_VERIFICATION,
        WhatsAppConcept.PHONE_NUMBER_MIGRATION,
        WhatsAppConcept.QUALITY_RATING,
        WhatsAppConcept.GREEN_TICK,
        WhatsAppConcept.WEBHOOK_CONFIG,
    ],
}
