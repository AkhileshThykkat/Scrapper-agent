"""
Step 5: Competitive intelligence — deep analysis of competitive positioning.
"""

from __future__ import annotations

import json
import logging

from review_intel.analysis.chain import AnalysisContext, AnalysisStep
from review_intel.domain.platform_registry import PLATFORMS

logger = logging.getLogger(__name__)


class CompetitiveIntelStep(AnalysisStep):
    """Extract deep competitive intelligence with evidence and reasoning."""

    @property
    def name(self) -> str:
        return "competitive_intel"

    async def execute(self, context: AnalysisContext) -> AnalysisContext:
        # Find reviews mentioning competitors + switching data
        competitor_names = [p.name for p in PLATFORMS.values()]
        mentions = []
        for r in context.reviews:
            text_lower = r.text.lower()
            mentioned = [
                name for name in competitor_names
                if name.lower() in text_lower and name.lower() != context.company.lower()
            ]
            if mentioned:
                mentions.append({"id": r.id[:8], "text": r.text[:400], "competitors": mentioned, "rating": r.rating})

        switching = []
        for ext in context.raw_extractions:
            sf = ext.get("switching_from")
            st = ext.get("switching_to")
            if sf or st:
                switching.append({"from": sf, "to": st, "ref": ext.get("review_ref", "")})

        if not mentions and not switching:
            logger.info("No competitor mentions found")
            return context

        prompt = f"""You are a competitive intelligence analyst studying how "{context.company}" is positioned relative to competitors.

REVIEWS MENTIONING COMPETITORS ({len(mentions)} found):
{json.dumps(mentions[:25])}

SWITCHING DATA:
{json.dumps(switching[:20])}

Produce a THOROUGH competitive analysis:

1. **competitive_advantages**: For each advantage {context.company} has over competitors:
   - advantage: what the advantage is
   - vs_competitors: which competitors this applies against
   - evidence: 2-3 direct quotes from reviews
   - explanation: 2-3 sentences on WHY this is an advantage and how significant it is

2. **competitive_disadvantages**: For each disadvantage:
   - disadvantage: what the weakness is
   - vs_competitors: which competitors are better at this
   - evidence: 2-3 direct quotes
   - explanation: 2-3 sentences on the significance and risk

3. **switching_analysis**: Analyze the switching patterns:
   - inbound: who is switching TO {context.company} and WHY (with quotes)
   - outbound: who is switching FROM {context.company} and WHY (with quotes)
   - net_direction: is {context.company} gaining or losing users on net?
   - key_switch_triggers: the top 3 reasons people switch, with explanation

4. **market_position_summary**: 3-5 sentence paragraph describing {context.company}'s competitive position in the market. Where does it sit? What's its moat? Where is it vulnerable?

5. **competitive_recommendations**: 3 specific, actionable recommendations for the product team based on competitive findings

Respond with JSON:
{{"competitive_advantages": [...], "competitive_disadvantages": [...], "switching_analysis": {{"inbound": [...], "outbound": [...], "net_direction": "...", "key_switch_triggers": [...]}}, "market_position_summary": "...", "competitive_recommendations": ["...", "...", "..."]}}"""

        raw = await self.llm.complete(prompt, "", max_tokens=4096)
        if raw:
            try:
                text = raw.strip()
                if text.startswith("```"):
                    text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
                context.competitive_intel = json.loads(text)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning("Competitive intel parse failed: %s", e)

        logger.info("Competitive intel extracted (%d keys)", len(context.competitive_intel))
        return context
