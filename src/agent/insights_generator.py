"""
insights_generator.py - Structured LLM Business Insights Generator

Generates concise, data-grounded business insights across six sections
using one structured LLM call with secondary LLM and deterministic fallbacks.
"""

import json
import logging
import re
import litellm

from src.agent.llm_config import (
    PRIMARY_MODEL_NAME,
    PRIMARY_LLM_API_KEY,
    PRIMARY_LLM_BASE_URL,
    SECONDARY_MODEL_NAME,
    SECONDARY_LLM_API_KEY,
    SECONDARY_LLM_BASE_URL,
)

logger = logging.getLogger(__name__)

SECTIONS = [
    "location_insights",
    "performance_insights",
    "competition_insights",
    "opportunity_insights",
    "financial_insights",
    "business_recommendations",
]


def _extract_summary(context: dict, analysis: dict) -> dict:
    """Extract and format verified analytical results into a simple summary dictionary."""
    loc = analysis.get("location_result") or {}
    perf = analysis.get("performance_result") or {}
    comp = analysis.get("competition_result") or {}
    comp_sum = comp.get("competition_summary") or {}
    opp = analysis.get("opportunity_result") or {}
    fin = analysis.get("financial_result") or analysis.get("financial") or {}

    pred_class = perf.get("prediction", "Unknown")
    probs = perf.get("probabilities") or {}
    raw_prob = probs.get(pred_class, 0.0)
    try:
        prob_val = float(raw_prob)
        prob_pct = round(prob_val * 100 if prob_val <= 1.0 else prob_val, 1)
    except (TypeError, ValueError):
        prob_pct = 0.0

    return {
        "location": context.get("location") or loc.get("location", "Bengaluru"),
        "cuisine": context.get("primary_cuisine", "Dining"),
        "rest_type": context.get("primary_rest_type", "Restaurant"),
        "cost_for_two": float(context.get("approx_cost_for_two") or context.get("approx_costfor_two_people") or 800),
        "loc_found": bool(loc.get("found", False)),
        "hist_restaurants": int(loc.get("historical_restaurant_count") or 0),
        "loc_median_cost": float(loc.get("location_median_cost") or 0),
        "online_order_pct": round(float(loc.get("location_online_order_rate") or 0) * 100, 1),
        "book_table_pct": round(float(loc.get("location_book_table_rate") or 0) * 100, 1),
        "pred_class": pred_class,
        "pred_prob_pct": prob_pct,
        "competitor_count": int(comp_sum.get("competitor_count_retrieved") or comp.get("competitor_count") or 0),
        "avg_rating": round(float(comp_sum.get("avg_competitor_rating") or 0), 2),
        "opp_score": round(float((opp.get("opportunity_score") or {}).get("score") or 0), 1),
        "opp_category": (opp.get("opportunity_score") or {}).get("signal", "Moderate"),
        "revenue": round(float(fin.get("monthly_revenue") or 0)),
        "profit": round(float(fin.get("estimated_operating_profit") or 0)),
        "margin": round(float(fin.get("operating_profit_margin") or 0), 1),
        "break_even": int(fin.get("break_even_target_customers_per_day") or fin.get("break_even_customers_per_day") or 0),
        "customers_per_day": int(fin.get("customers_per_day") or 100),
    }


def _get_fallback_insights(d: dict) -> dict:
    """Generate deterministic, data-grounded insights when LLMs are unavailable."""
    # 1. Location
    if d["loc_found"]:
        loc = [
            f"{d['location']} has {d['hist_restaurants']} historical restaurants recorded with a median cost of ₹{int(d['loc_median_cost']):,} for two.",
            f"Online ordering adoption is {d['online_order_pct']}%, while table reservations stand at {d['book_table_pct']}%.",
            f"Your proposed cost of ₹{int(d['cost_for_two']):,} aligns with local dining demand.",
        ]
    else:
        loc = [
            f"No historical Zomato benchmark records were found for {d['location']}.",
            "Local footfall and demand should be verified on-site before finalizing lease terms.",
            "Rely on live competitor density and nearby foot traffic to guide your price point.",
        ]

    # 2. Performance
    perf = [
        f"The Random Forest model predicts a {d['pred_class']} performance tier with a {d['pred_prob_pct']}% predicted-class probability.",
        "This probability reflects similarity to historical peer tiers, not overall model accuracy or guaranteed revenue.",
        "Execution, food quality, and service consistency will drive real-world financial results.",
    ]

    # 3. Competition
    comp = [
        f"Identified {d['competitor_count']} nearby competitors with an average Google rating of {d['avg_rating']} stars.",
        "Local incumbents have established strong customer followings in this immediate area.",
        "Focus on signature menu items and fast order fulfillment to differentiate from nearby options.",
    ]

    # 4. Opportunity
    opp = [
        f"The composite Opportunity Score is {d['opp_score']}/100, placing the concept in the {d['opp_category']} opportunity tier.",
        "This score combines historical performance signals (60% weight) with local competition headwinds (40% weight).",
        "Targeting an underserved micro-niche or strong delivery presence will help maximize market capture.",
    ]

    # 5. Financial
    profit_text = f"profit of ₹{d['profit']:,}" if d['profit'] >= 0 else f"loss of ₹{abs(d['profit']):,}"
    fin = [
        f"Estimated monthly revenue is ₹{d['revenue']:,} with an estimated operating {profit_text} ({d['margin']}% margin) at {d['customers_per_day']} daily covers.",
        f"The estimated break-even target is {d['break_even']} customers per day to cover all fixed and variable expenses.",
        "All figures are directional estimates based on operating assumptions and exclude taxes and aggregator commissions.",
    ]

    # 6. Recommendations
    rec = [
        f"Opportunity: Capitalize on {d['cuisine']} demand in {d['location']} with pricing matching local spending.",
        f"Risk: High competitor density ({d['competitor_count']} outlets) leaves little margin for operational inconsistency.",
        "Next Step: Validate physical footfall at peak hours and stress-test assumptions using What-If Scenarios.",
    ]

    return {
        "location_insights": loc,
        "performance_insights": perf,
        "competition_insights": comp,
        "opportunity_insights": opp,
        "financial_insights": fin,
        "business_recommendations": rec,
    }


def _build_prompt(d: dict) -> str:
    """Build a concise, structured prompt containing all verified numbers."""
    return f"""You are a restaurant business advisor for Bengaluru.
Analyze this verified data and generate 2 to 3 concise, insightful bullet points for each of the 6 sections.

DATA:
- Concept: {d['cuisine']} ({d['rest_type']}) in {d['location']} at ₹{int(d['cost_for_two'])} for two
- Location: {d['hist_restaurants']} historical restaurants, median cost ₹{int(d['loc_median_cost'])}, {d['online_order_pct']}% online ordering, {d['book_table_pct']}% table booking (Found: {d['loc_found']})
- ML Performance: Class "{d['pred_class']}" with {d['pred_prob_pct']}% predicted-class probability (do NOT call this model accuracy; never mention SHAP)
- Competition: {d['competitor_count']} competitors nearby with {d['avg_rating']} average rating
- Opportunity Score: {d['opp_score']}/100 ({d['opp_category']} tier)
- Financial: ₹{d['revenue']:,} monthly revenue, ₹{d['profit']:,} operating profit ({d['margin']}% margin), break-even at {d['break_even']} customers/day

Return ONLY a JSON object with these exact 6 keys, each containing an array of 2-3 short bullet strings:
{{
  "location_insights": ["..."],
  "performance_insights": ["..."],
  "competition_insights": ["..."],
  "opportunity_insights": ["..."],
  "financial_insights": ["..."],
  "business_recommendations": ["..."]
}}
"""


def _parse_llm_json(raw_text: str) -> dict:
    """Parse JSON from the LLM output, handling markdown code fences or surrounding text."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _call_llm(model: str, key: str | None, base_url: str | None, prompt: str, max_tokens: int) -> dict:
    """Invoke LiteLLM and parse JSON response."""
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    if key:
        kwargs["api_key"] = key
    if base_url:
        kwargs["api_base"] = base_url
    if "gpt-oss" in model.lower():
        kwargs["reasoning_effort"] = "low"

    response = litellm.completion(**kwargs)
    raw = response.choices[0].message.content or ""
    return _parse_llm_json(raw)


def generate_business_insights(context: dict, analysis: dict) -> dict:
    """
    Generate section-wise business insights across all 6 sections using ONE structured LLM call,
    with automatic secondary LLM fallback and deterministic Python fallback.
    """
    summary = _extract_summary(context, analysis)
    fallback = _get_fallback_insights(summary)
    prompt = _build_prompt(summary)

    parsed = None
    source = "deterministic_fallback"

    # 1. Primary LLM attempt
    if PRIMARY_LLM_API_KEY:
        try:
            parsed = _call_llm(PRIMARY_MODEL_NAME, PRIMARY_LLM_API_KEY, PRIMARY_LLM_BASE_URL, prompt, max_tokens=3000)
            source = "llm_primary"
        except Exception as e:
            logger.warning("Primary LLM (%s) failed: %s", PRIMARY_MODEL_NAME, e)

    # 2. Secondary LLM fallback
    if parsed is None and (SECONDARY_LLM_API_KEY or PRIMARY_LLM_API_KEY):
        try:
            sec_key = SECONDARY_LLM_API_KEY or PRIMARY_LLM_API_KEY
            parsed = _call_llm(SECONDARY_MODEL_NAME, sec_key, SECONDARY_LLM_BASE_URL, prompt, max_tokens=900)
            source = "llm_secondary"
        except Exception as e:
            logger.warning("Secondary LLM (%s) failed: %s", SECONDARY_MODEL_NAME, e)

    # 3. Assemble final result ensuring 2-3 clean bullets per section
    result = {"_insights_source": source}
    for key in SECTIONS:
        bullets = parsed.get(key) if isinstance(parsed, dict) else None
        if isinstance(bullets, list) and len(bullets) >= 2:
            cleaned = [re.sub(r"^[-*•]\s*", "", str(b)).strip() for b in bullets if str(b).strip()]
            result[key] = cleaned[:3] if len(cleaned) >= 2 else fallback[key]
        else:
            result[key] = fallback[key]

    return result
