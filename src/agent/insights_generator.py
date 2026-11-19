import json
import logging
import re
from typing import Any, Dict
import litellm

from src.agent.llm_config import (
    PRIMARY_MODEL_NAME,
    PRIMARY_LLM_API_KEY,
    PRIMARY_LLM_BASE_URL,
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


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    try:
        return int(float(val)) if val is not None else default
    except (TypeError, ValueError):
        return default


def _empty_insights(source: str = "unavailable") -> dict:
    """Return an empty insight structure compatible with the frontend."""
    return {
        "location_insights": [],
        "performance_insights": [],
        "competition_insights": [],
        "opportunity_insights": [],
        "financial_insights": [],
        "business_recommendations": [],
        "_insights_source": source,
    }


def _extract_summary(context: dict, analysis: dict) -> dict:
    """Extract and normalize metrics for the LLM prompt."""
    loc = analysis.get("location_result") or {}
    perf = analysis.get("performance_result") or {}
    comp = (analysis.get("competition_result") or {}).get("competition_summary") or {}
    opp = analysis.get("opportunity_result") or {}
    fin = analysis.get("financial_result") or analysis.get("financial") or {}

    pred = str(perf.get("prediction") or "Unknown")
    probs = perf.get("probabilities") or {}
    prob_val = _safe_float(probs.get(pred, 0.0))
    prob_pct = round(prob_val * 100 if prob_val <= 1.0 else prob_val, 1)

    location = str(context.get("location") or loc.get("location") or "the target area").strip()

    return {
        "location": location,
        "cuisine": str(context.get("primary_cuisine") or "Dining").strip(),
        "rest_type": str(context.get("primary_rest_type") or "Restaurant").strip(),
        "cost_for_two": _safe_int(context.get("approx_cost_for_two") or 800),
        "hist_restaurants": _safe_int(loc.get("historical_restaurant_count")),
        "loc_median_cost": _safe_int(loc.get("location_median_cost")),
        "online_order_pct": round(_safe_float(loc.get("location_online_order_rate")) * 100, 1),
        "book_table_pct": round(_safe_float(loc.get("location_book_table_rate")) * 100, 1),
        "pred_class": pred,
        "pred_prob_pct": prob_pct,
        "competitor_count": _safe_int(comp.get("competitor_count_retrieved")),
        "avg_rating": round(_safe_float(comp.get("avg_competitor_rating")), 2),
        "opp_score": round(_safe_float((opp.get("opportunity_score") or {}).get("score")), 1),
        "opp_category": str((opp.get("opportunity_score") or {}).get("signal") or "Moderate"),
        "revenue": _safe_int(fin.get("monthly_revenue")),
        "profit": _safe_int(fin.get("estimated_operating_profit")),
        "margin": round(_safe_float(fin.get("operating_profit_margin")), 1),
        "break_even": _safe_int(fin.get("break_even_target_customers_per_day") or fin.get("break_even_customers_per_day")),
    }


def _build_prompt(d: dict) -> str:
    """Build a concise, structured prompt containing verified analysis data."""
    loc = d["location"]
    return f"""You are a restaurant business advisor for {loc}.
Analyze this verified data and generate concise, insightful bullet points for each section.

DATA:
- Concept: {d['cuisine']} ({d['rest_type']}) in {loc} at ₹{d['cost_for_two']} for two
- Location: {d['hist_restaurants']} restaurants, median cost ₹{d['loc_median_cost']}, {d['online_order_pct']}% online ordering, {d['book_table_pct']}% booking
- ML Prediction: Class "{d['pred_class']}" ({d['pred_prob_pct']}% probability)
- Competition: {d['competitor_count']} competitors nearby with {d['avg_rating']} average rating
- Opportunity Score: {d['opp_score']}/100 ({d['opp_category']} tier)
- Financials: ₹{d['revenue']:,} revenue, ₹{d['profit']:,} operating profit ({d['margin']}% margin), break-even at {d['break_even']} covers/day

Return ONLY a JSON object with these exact keys:
{{
  "location_insights": ["...", "..."],
  "performance_insights": ["...", "..."],
  "competition_insights": ["...", "..."],
  "opportunity_insights": ["...", "..."],
  "financial_insights": ["...", "..."],
  "business_recommendations": [
    "Key Insight: <opportunity>",
    "Key Risk: <primary risk>",
    "Recommendation: <actionable next step>"
  ]
}}"""


def _parse_json(text: str) -> dict:
    """Parse JSON from the LLM output, handling markdown fences or substring JSON."""
    clean = (text or "").strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()
    try:
        return json.loads(clean)
    except Exception:
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end > start:
            return json.loads(clean[start : end + 1])
        raise


def generate_business_insights(context: dict, analysis: dict) -> dict:
    """
    Generate structured business insights using one Primary LLM call.
    If the LLM fails, returns an empty insight structure safely.
    """
    if not PRIMARY_LLM_API_KEY:
        logger.warning("Primary LLM API key not configured. Skipping insights generation.")
        return _empty_insights("missing_api_key")

    try:
        summary = _extract_summary(context or {}, analysis or {})
        prompt = _build_prompt(summary)

        kwargs: Dict[str, Any] = {
            "model": PRIMARY_MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2500,
            "api_key": PRIMARY_LLM_API_KEY,
        }
        if PRIMARY_LLM_BASE_URL:
            kwargs["api_base"] = PRIMARY_LLM_BASE_URL
        if "gpt-oss" in PRIMARY_MODEL_NAME.lower():
            kwargs["reasoning_effort"] = "low"

        response = litellm.completion(**kwargs)
        raw_text = response.choices[0].message.content or ""
        parsed = _parse_json(raw_text)

        if not isinstance(parsed, dict):
            logger.warning("Primary LLM returned non-dictionary JSON.")
            return _empty_insights("invalid_llm_output")

        result = {"_insights_source": "llm_primary"}
        for key in SECTIONS:
            items = parsed.get(key)
            if isinstance(items, list):
                cleaned = [re.sub(r"^[-*•]\s*", "", str(x)).strip() for x in items if str(x).strip()]
                result[key] = cleaned[:3]
            else:
                result[key] = []

        # Ensure business_recommendations has Key Insight, Key Risk, Recommendation labels
        recs = result["business_recommendations"]
        if len(recs) >= 3:
            labels = ["Key Insight", "Key Risk", "Recommendation"]
            result["business_recommendations"] = [
                f"{label}: {item}" if not re.match(r"^(key insight|insight|key risk|risk|recommendation|next step)\s*:", item, re.IGNORECASE) else item
                for label, item in zip(labels, recs[:3])
            ]

        return result

    except Exception as e:
        logger.warning("Primary LLM (%s) insight generation failed: %s", PRIMARY_MODEL_NAME, e)
        return _empty_insights("error")
