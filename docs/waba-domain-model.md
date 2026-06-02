# WABA Domain Model

**Purpose:** Encode WhatsApp Business API ecosystem knowledge for automated review classification, LLM context injection, and competitive analysis.

---

## 1. Target Platform Registry

### WhatsApp Business Solution Providers (BSPs)

| Platform | Category | API Type | Primary Market | Key Differentiator |
|---|---|---|---|---|
| **Interakt** | BSP + CRM | Cloud API | India SMB | Shopify integration, affordable pricing |
| **Wati** | BSP + Inbox | Cloud API | Global SMB/Mid | Easy setup, team inbox |
| **AiSensy** | BSP + Marketing | Cloud API | India SMB | Broadcast focus, affordable |
| **Gallabox** | BSP + Commerce | Cloud API | India SMB | Commerce features, shared inbox |
| **DoubleTick** | BSP + Sales | Cloud API | India SMB | Green tick, sales CRM |
| **Gupshup** | CPaaS | Cloud API | Enterprise | Multi-channel, conversation AI |
| **Respond.io** | Omnichannel Inbox | Cloud API | Global Mid/Enterprise | Multi-channel inbox |
| **SleekFlow** | Social Commerce | Cloud API | APAC | Social selling, commerce |
| **MessageBird** | CPaaS | Cloud API | Global Enterprise | Omnichannel, APIs |
| **Twilio** | CPaaS | Cloud API | Global Enterprise | Developer-first, APIs |

### CRM & Support Platforms with WhatsApp Integration

| Platform | Category | WhatsApp Integration Type |
|---|---|---|
| **Freshchat** | Support | Native WhatsApp channel |
| **HubSpot** | CRM | WhatsApp integration via partners |
| **Zendesk** | Support | WhatsApp Business channel |
| **Salesforce** | CRM | WhatsApp via Digital Engagement |
| **Meta WhatsApp Business Platform** | Platform | Direct Cloud API / On-Premise API |

---

## 2. WhatsApp Business Concept Taxonomy

### 2.1 Messaging & Conversations

```yaml
conversations:
  categories:
    - marketing: "Business-initiated, promotional messages"
    - utility: "Business-initiated, transactional/service updates"
    - authentication: "OTP and verification messages"
    - service: "User-initiated conversations (free 24h window)"
  
  concepts:
    - conversation_window: "24-hour response window"
    - messaging_limits: "Tier 1 (1K), Tier 2 (10K), Tier 3 (100K), Unlimited"
    - quality_rating: "Green, Yellow, Red quality scores"
    - per_conversation_pricing: "Pricing model based on conversation type"
```

### 2.2 Templates

```yaml
templates:
  types:
    - marketing_template: "Promotional messages requiring approval"
    - utility_template: "Transactional updates requiring approval"
    - authentication_template: "OTP templates with special approval"
  
  concepts:
    - template_approval: "Meta review process for message templates"
    - template_rejection: "Common rejection reasons and appeals"
    - template_categories: "Header, body, footer, buttons structure"
    - template_variables: "Dynamic content placeholders"
    - template_quality: "Template quality scoring by Meta"
    - rich_media_templates: "Image, video, document headers"
    - interactive_templates: "Quick reply and CTA button templates"
```

### 2.3 Engagement Features

```yaml
engagement:
  broadcast:
    - broadcast_campaigns: "Bulk message sending to opted-in users"
    - broadcast_scheduling: "Timed campaign delivery"
    - broadcast_analytics: "Delivery, read, response tracking"
    - broadcast_segmentation: "Audience targeting and segmentation"
  
  click_to_whatsapp:
    - ctwa_ads: "Facebook/Instagram ads that open WhatsApp"
    - ctwa_tracking: "Attribution and conversion tracking"
    - ctwa_workflows: "Automated responses to ad clicks"
  
  flows:
    - whatsapp_flows: "Interactive multi-step forms in WhatsApp"
    - flow_builder: "Visual flow design tools"
    - flow_messages: "Flow-based interactive messages"
  
  interactive:
    - quick_replies: "Up to 3 button options"
    - list_messages: "Scrollable list selections"
    - cta_buttons: "Call-to-action URL/phone buttons"
    - location_messages: "Location sharing and requests"
```

### 2.4 Platform Operations

```yaml
operations:
  team:
    - shared_inbox: "Multi-agent conversation management"
    - agent_assignment: "Automatic/manual conversation routing"
    - multi_agent_support: "Concurrent agent access"
    - agent_performance: "Response time and resolution tracking"
    - canned_responses: "Pre-built reply templates"
  
  automation:
    - chatbot_builder: "No-code/low-code bot creation"
    - flow_builder_automation: "Automated conversation flows"
    - keyword_triggers: "Keyword-based auto-responses"
    - business_hours: "Operating hours and away messages"
    - auto_assignment: "Rule-based conversation routing"
  
  integrations:
    - crm_sync: "CRM contact and deal synchronization"
    - ecommerce_integration: "Shopify, WooCommerce connections"
    - payment_integration: "Payment gateway connections"
    - webhook_support: "Custom webhook configurations"
    - api_access: "REST API for custom integrations"
    - zapier_integration: "No-code automation connections"
```

### 2.5 Commerce

```yaml
commerce:
  - catalog_support: "Product catalog display in WhatsApp"
  - product_messages: "Single and multi-product messages"
  - order_messages: "Order confirmation and tracking"
  - payment_collection: "In-chat payment processing"
  - cart_management: "Shopping cart in WhatsApp"
```

### 2.6 Platform Setup

```yaml
setup:
  - embedded_signup: "Streamlined Meta business verification"
  - business_verification: "Meta Business Manager verification"
  - phone_number_migration: "Number porting between BSPs"
  - green_tick: "Official Business Account verification"
  - display_name: "Business display name approval"
```

### 2.7 Analytics & Reporting

```yaml
analytics:
  - conversation_analytics: "Message volume, response metrics"
  - campaign_analytics: "Broadcast performance tracking"
  - agent_analytics: "Agent performance dashboards"
  - revenue_attribution: "Revenue tracking from WhatsApp"
  - funnel_analytics: "Conversion funnel tracking"
```

---

## 3. Review Classification Keywords

### Keyword Maps for WABA Theme Detection

```python
WABA_KEYWORD_MAP: dict[str, list[str]] = {
    "broadcast_campaigns": [
        "broadcast", "bulk message", "mass message", "campaign",
        "bulk send", "promotional message", "marketing message",
        "newsletter", "announcement", "blast",
    ],
    "template_management": [
        "template", "message template", "pre-approved",
        "template format", "template variable", "dynamic content",
        "header template", "media template",
    ],
    "template_approvals": [
        "template approval", "template reject", "pending approval",
        "meta approval", "template review", "approval process",
        "template status", "rejected template", "appeal",
    ],
    "ctwa_workflows": [
        "click to whatsapp", "ctwa", "whatsapp ad", "facebook ad",
        "instagram ad", "ad click", "click-to-chat",
        "ad integration", "lead from ad",
    ],
    "shared_inbox": [
        "shared inbox", "team inbox", "multi-agent",
        "agent assignment", "conversation routing", "queue",
        "team collaboration", "assign conversation",
    ],
    "chatbot_builder": [
        "chatbot", "bot builder", "no-code bot", "auto reply",
        "automated response", "conversation bot", "ai bot",
        "chat automation", "bot flow",
    ],
    "flow_builder": [
        "flow builder", "workflow", "automation flow",
        "whatsapp flow", "interactive flow", "form flow",
        "multi-step", "conversation flow",
    ],
    "integrations": [
        "integration", "connect", "sync", "api",
        "webhook", "zapier", "shopify", "woocommerce",
        "hubspot", "salesforce", "zoho", "pipedrive",
    ],
    "crm_sync": [
        "crm", "contact sync", "lead management",
        "deal tracking", "pipeline", "contact management",
        "customer data", "contact import",
    ],
    "catalog_support": [
        "catalog", "product catalog", "product message",
        "product list", "shopping", "ecommerce",
        "product display", "multi-product",
    ],
    "commerce": [
        "commerce", "order", "payment", "cart",
        "checkout", "purchase", "buy", "sell",
        "transaction", "invoice",
    ],
    "automation": [
        "automation", "automate", "auto", "trigger",
        "rule", "workflow", "scheduled", "automatic",
        "smart", "intelligent routing",
    ],
    "webhooks": [
        "webhook", "callback", "event notification",
        "real-time update", "push notification",
        "api callback", "event hook",
    ],
    "api_reliability": [
        "api", "uptime", "downtime", "outage",
        "server error", "500 error", "timeout",
        "rate limit", "api speed", "latency",
        "reliability", "stability",
    ],
    "multi_agent": [
        "multi-agent", "multiple agent", "team member",
        "agent seat", "user seat", "team size",
        "concurrent agent", "agent limit",
    ],
    "reporting": [
        "report", "analytics", "dashboard", "metrics",
        "statistics", "insight", "data", "chart",
        "graph", "export", "download report",
    ],
    "pricing": [
        "price", "pricing", "cost", "expensive",
        "affordable", "cheap", "plan", "subscription",
        "billing", "invoice", "charge", "fee",
        "free trial", "discount", "value for money",
    ],
    "onboarding": [
        "onboarding", "setup", "getting started",
        "documentation", "tutorial", "guide",
        "learning curve", "easy to set up",
        "difficult to set up", "configuration",
    ],
}
```

---

## 4. WhatsApp Ecosystem Events

The system should recognize and tag reviews discussing these ecosystem-level changes:

| Event Category | Examples |
|---|---|
| **API Changes** | Cloud API migration, On-Premise deprecation, new API versions |
| **Pricing Changes** | Per-conversation pricing updates, free tier changes |
| **Policy Changes** | Template approval policy updates, opt-in requirements |
| **Feature Launches** | WhatsApp Flows, Commerce features, Channel features |
| **Compliance** | Business verification requirements, data residency |
| **Platform Issues** | API outages, template approval delays, messaging limit changes |

---

## 5. Competitive Dimensions for WABA Platforms

When comparing WABA platforms, evaluate across these dimensions:

| Dimension | Key Metrics |
|---|---|
| **Ease of Use** | Setup time, learning curve, UI intuitiveness |
| **Pricing** | Monthly cost, per-conversation cost, included features |
| **Template Management** | Approval speed, template builder quality, template analytics |
| **Broadcast Capability** | Segmentation, scheduling, analytics, A/B testing |
| **Automation** | Bot builder quality, flow complexity, trigger options |
| **Team Collaboration** | Inbox UX, assignment rules, agent metrics |
| **Integrations** | CRM, e-commerce, payment, custom API quality |
| **Analytics** | Dashboard depth, export options, real-time data |
| **Customer Support** | Response time, channel availability, knowledge base |
| **Reliability** | Uptime, message delivery rate, API stability |
| **Scalability** | Message volume limits, API rate limits, concurrent users |
| **Commerce** | Catalog support, payment integration, order management |
