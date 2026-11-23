import json
import logging
import re
from typing import Any, Dict

import litellm

from src.agent.llm_config import (
    PRIMARY_LLM_API_KEY,
    PRIMARY_LLM_BASE_URL,
    PRIMARY_MODEL_NAME,
)

logger = logging.getLogger(__name__)

VALID_VERDICTS = {"Promising", "Risky", "Not Recommended"}

# Safe type helpers (self-contained so this module has no internal deps)
def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(float(val)) if val is not None else default
    except (TypeError, ValueError):
        return default


# Returned when the LLM cannot produce a verdict
def _unavailable(source: str) -> dict:
    """Safe empty verdict. 'source' explains why (e.g. 'error', 'missing_api_key')."""
    return {
        "verdict": "unavailable",
        "explanation": "",
        "strengths": [],
        "risks": [],
        "recommendation": "",
        "_judge_source": source,
    }


# Step 1 — Flatten the four permitted specialist results into a prompt-ready dict
def _extract_metrics(analysis: dict, context: dict) -> dict:
    """
    Pull the key data points from the four permitted specialist results.
    Financial simulator data is never read here — it is excluded by design.
    """
    loc  = analysis.get("location_result")    or {}
    perf = analysis.get("performance_result") or {}
    comp = (analysis.get("competition_result") or {}).get("competition_summary") or {}
    opp  = analysis.get("opportunity_result") or {}

    # ML performance prediction
    pred     = str(perf.get("prediction") or "Unknown")
    probs    = perf.get("probabilities") or {}
    prob_val = _safe_float(probs.get(pred, 0.0))
    pred_pct = round(prob_val * 100 if prob_val <= 1.0 else prob_val, 1)

    # Opportunity score
    opp_score_obj = opp.get("opportunity_score") or {}

    return {
        # Concept
        "location":     str(context.get("location")         or loc.get("location") or "the target area").strip(),
        "cuisine":      str(context.get("primary_cuisine")   or "Dining").strip(),
        "rest_type":    str(context.get("primary_rest_type") or "Restaurant").strip(),
        "cost_for_two": _safe_int(context.get("approx_cost_for_two") or 800),
        # Location suitability
        "hist_restaurants": _safe_int(loc.get("historical_restaurant_count")),
        "loc_median_cost":  _safe_int(loc.get("location_median_cost")),
        "online_pct":       round(_safe_float(loc.get("location_online_order_rate")) * 100, 1),
        "book_table_pct":   round(_safe_float(loc.get("location_book_table_rate"))   * 100, 1),
        # ML prediction
        "pred_class": pred,
        "pred_pct":   pred_pct,
        # Competition
        "competitor_count": _safe_int(comp.get("competitor_count_retrieved")),
        "avg_rating":       round(_safe_float(comp.get("avg_competitor_rating")), 2),
        "high_rating_comp": _safe_int(comp.get("high_rating_competitors")),
        # Opportunity
        "opp_score":  round(_safe_float(opp_score_obj.get("score")), 1),
        "opp_signal": str(opp_score_obj.get("signal") or "Moderate"),
    }


# Step 2 — Build the LLM prompt
def _build_prompt(m: dict) -> str:
    """
    Builds the judge prompt from the flattened metrics.
    Only location, ML performance, competition, and opportunity data are included.
    Revenue, profit, margins, and break-even figures are intentionally absent.
    """
    return f"""You are a friendly, experienced restaurant business advisor helping a restaurant owner make an informed decision.

A new restaurant concept has been evaluated by four independent specialist analyses. Your job is to review their findings and give a clear, honest final verdict.

SPECIALIST FINDINGS:
- Concept: {m['cuisine']} ({m['rest_type']}) at ₹{m['cost_for_two']} for two, in {m['location']}
- Location suitability: {m['hist_restaurants']} restaurants recorded in this area, local median cost ₹{m['loc_median_cost']}, {m['online_pct']}% offer online ordering, {m['book_table_pct']}% offer table booking
- Performance prediction: The restaurant model predicts a "{m['pred_class']}" outcome ({m['pred_pct']}% probability)
- Competition: {m['competitor_count']} active competitors nearby, average rating {m['avg_rating']}★, {m['high_rating_comp']} rated ≥4.5★
- Opportunity score: {m['opp_score']}/100 ({m['opp_signal']} tier)

HOW TO WRITE YOUR EVALUATION:
- Consider all four findings together — do not focus on just one number.
- Write the explanation in plain, friendly language a restaurant owner can immediately understand (4–5 short, natural sentences).
- Do not use technical ML terms like "classifier", "probability distribution", or "feature vector".
- You MUST evaluate both strengths and risks separately:
  * strengths: 2–3 concise bullet points identifying positive factors from the specialist analysis (e.g. strong local demand, high opportunity score, favorable predicted outcome tier).
  * risks: 2–3 concise bullet points identifying negative factors, weaknesses, uncertainties, market saturation, competitor barriers, or business limitations from the specialist analysis.
  * Do NOT put risks inside strengths or combine both into one field. Both lists must be returned separately.
- Keep the recommendation as one practical action the owner can take this week.
- Do not add revenue, profit, or financial figures — those are outside the scope of this evaluation.

VERDICT OPTIONS (pick exactly one):
- "Promising"        — the evidence is broadly positive; this concept has real potential.
- "Risky"            — there are notable concerns, but the concept is not ruled out.
- "Not Recommended"  — the evidence suggests significant barriers that make this difficult to overcome.

Return ONLY this JSON format (no markdown, no extra text):
{{
  "verdict": "Promising",
  "explanation": "Your restaurant idea looks promising in this location because demand indicators are encouraging and competition is manageable. However, some market challenges need careful attention. Focus on building customer loyalty and differentiating your restaurant from nearby competitors. Overall, the business has potential, but success is not guaranteed.",
  "strengths": [
    "Encouraging local demand with high online ordering adoption",
    "Favorable opportunity score indicating market space for this cuisine"
  ],
  "risks": [
    "Established competitors with high ratings already capture significant footfall",
    "Moderate table booking culture in the area may limit dine-in reservations"
  ],
  "recommendation": "Conduct a 30-day pilot with a focused delivery-only menu before committing to a full fit-out."
}}"""

# Step 3 — Parse JSON from raw LLM output (handles markdown fences)
def _parse_json(text: str) -> dict:
    clean = (text or "").strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()
    try:
        return json.loads(clean)
    except Exception:
        start, end = clean.find("{"), clean.rfind("}")
        if start != -1 and end > start:
            return json.loads(clean[start : end + 1])
        raise

# Public entry point
def generate_judge_verdict(analysis: dict, context: dict) -> dict:
    """
    Generate a final business verdict using the Primary LLM.

    Parameters
    ----------
    analysis : dict
        Must contain only the four permitted specialist results:
        location_result, performance_result, competition_result, opportunity_result.
        Financial simulator output must NOT be passed here.
    context : dict
        Concept metadata: location, primary_cuisine, primary_rest_type,
        approx_cost_for_two, online_order, book_table.

    Returns
    -------
    dict
        Keys: verdict, explanation, strengths, risks, recommendation, _judge_source.
        On failure: verdict = "unavailable", no fake Python judgement is generated.
    """
    if not PRIMARY_LLM_API_KEY:
        logger.warning("Judge Agent: Primary LLM API key not configured.")
        return _unavailable("missing_api_key")

    if not analysis or not isinstance(analysis, dict):
        logger.warning("Judge Agent: No analysis data provided.")
        return _unavailable("incomplete_data")

    try:
        metrics  = _extract_metrics(analysis, context or {})
        prompt   = _build_prompt(metrics)

        # LiteLLM call — same pattern used in insights_generator.py
        kwargs: Dict[str, Any] = {
            "model":       PRIMARY_MODEL_NAME,
            "messages":    [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens":  600,
            "api_key":     PRIMARY_LLM_API_KEY,
        }
        if PRIMARY_LLM_BASE_URL:
            kwargs["api_base"] = PRIMARY_LLM_BASE_URL
        if "gpt-oss" in PRIMARY_MODEL_NAME.lower():
            kwargs["reasoning_effort"] = "low"

        response = litellm.completion(**kwargs)
        raw      = response.choices[0].message.content or ""
        parsed   = _parse_json(raw)

        if not isinstance(parsed, dict):
            logger.warning("Judge Agent: LLM returned non-dict JSON.")
            return _unavailable("invalid_llm_output")

        verdict = str(parsed.get("verdict", "")).strip()
        if verdict not in VALID_VERDICTS:
            logger.warning("Judge Agent: Unexpected verdict value '%s'.", verdict)
            return _unavailable("invalid_verdict")

        strengths_raw = parsed.get("strengths")
        risks_raw = parsed.get("risks")

        strengths = [str(s).strip() for s in strengths_raw if str(s).strip()] if isinstance(strengths_raw, list) else []
        risks = [str(r).strip() for r in risks_raw if str(r).strip()] if isinstance(risks_raw, list) else []

        return {
            "verdict":        verdict,
            "explanation":    str(parsed.get("explanation") or "").strip(),
            "strengths":      strengths,
            "risks":          risks,
            "recommendation": str(parsed.get("recommendation") or "").strip(),
            "_judge_source":  "llm_primary",
        }

    except Exception as exc:
        logger.warning("Judge Agent: Failed to generate verdict: %s", exc)
        return _unavailable("error")
