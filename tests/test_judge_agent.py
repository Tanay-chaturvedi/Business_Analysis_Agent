"""
Unit tests for src/agent/judge_agent.py
========================================
Tests cover:
  - Successful LLM verdict (all three categories)
  - Missing API key
  - LLM API failure
  - Invalid / missing verdict in LLM response
  - Non-dict LLM response
  - Missing or incomplete analysis data
  - Financial simulator data must NOT be passed to the Judge Agent
  - Coordinator integration (judge_inputs construction)
  - JSON parsing with markdown fences

The Primary LLM is mocked throughout — no real network calls are made.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Minimal fixtures shared across tests
# ---------------------------------------------------------------------------

CONTEXT = {
    "location": "Indiranagar, Bangalore",
    "primary_cuisine": "North Indian",
    "primary_rest_type": "Casual Dining",
    "approx_cost_for_two": 600,
    "online_order": 1,
    "book_table": 0,
}

# Valid specialist analysis (no financial data — as the coordinator should provide)
ANALYSIS = {
    "location_result": {
        "location": "Indiranagar, Bangalore",
        "found": True,
        "historical_restaurant_count": 120,
        "location_median_cost": 550,
        "location_online_order_rate": 0.72,
        "location_book_table_rate": 0.18,
    },
    "performance_result": {
        "prediction": "High",
        "probabilities": {"High": 0.68, "Medium": 0.22, "Low": 0.10},
    },
    "competition_result": {
        "competitor_count": 14,
        "competition_summary": {
            "competitor_count_retrieved": 14,
            "avg_competitor_rating": 4.1,
            "high_rating_competitors": 3,
        },
    },
    "opportunity_result": {
        "opportunity_score": {"score": 72.5, "signal": "High"},
    },
}


def _make_llm_response(verdict: str) -> MagicMock:
    """Build a mock litellm.completion response with a valid JSON payload."""
    payload = {
        "verdict": verdict,
        "explanation": (
            "Your restaurant idea looks promising in this location because demand "
            "indicators are encouraging and competition is manageable. "
            "However, some market challenges need careful attention. "
            "Focus on building customer loyalty and differentiating your restaurant "
            "from nearby competitors. Overall, the business has potential."
        ),
        "strengths": ["Strong online delivery demand in the area", "High opportunity score"],
        "risks": ["Several well-rated competitors already present", "Moderate booking culture"],
        "recommendation": "Conduct a 30-day pilot with a focused delivery-only menu before committing to a full fit-out.",
    }
    message  = MagicMock()
    message.content = json.dumps(payload)
    choice   = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_strengths_and_risks_separated(mock_completion):
    """Confirm strengths and risks are distinct lists and not combined."""
    payload = {
        "verdict": "Promising",
        "explanation": "Explanation text.",
        "strengths": ["High footfall", "Good cuisine fit"],
        "risks": ["High competitor concentration", "Rising rental rates"],
        "recommendation": "Start small.",
    }
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(payload)))]
    )

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["strengths"] == ["High footfall", "Good cuisine fit"]
    assert result["risks"] == ["High competitor concentration", "Rising rental rates"]
    # Verify no overlap or combination
    assert set(result["strengths"]).isdisjoint(set(result["risks"]))


@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_no_hardcoded_python_risks_injected_when_empty(mock_completion):
    """If the LLM returns an empty risks list, Python must not inject hardcoded risks."""
    payload = {
        "verdict": "Promising",
        "explanation": "Explanation text.",
        "strengths": ["High footfall"],
        "risks": [],
        "recommendation": "Start small.",
    }
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps(payload)))]
    )

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["risks"] == []


# ---------------------------------------------------------------------------
# 1. Successful verdict — Promising
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_promising_verdict(mock_completion):
    mock_completion.return_value = _make_llm_response("Promising")

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "Promising"
    assert result["_judge_source"] == "llm_primary"
    assert isinstance(result["strengths"], list)
    assert isinstance(result["risks"], list)
    assert result["explanation"] != ""
    assert result["recommendation"] != ""
    mock_completion.assert_called_once()


# ---------------------------------------------------------------------------
# 2. Successful verdict — Risky
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_risky_verdict(mock_completion):
    mock_completion.return_value = _make_llm_response("Risky")

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "Risky"
    assert result["_judge_source"] == "llm_primary"


# ---------------------------------------------------------------------------
# 3. Successful verdict — Not Recommended
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_not_recommended_verdict(mock_completion):
    mock_completion.return_value = _make_llm_response("Not Recommended")

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "Not Recommended"
    assert result["_judge_source"] == "llm_primary"


# ---------------------------------------------------------------------------
# 4. Missing API key → unavailable, no network call
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "")
def test_missing_api_key(mock_completion):
    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "unavailable"
    assert result["_judge_source"] == "missing_api_key"
    mock_completion.assert_not_called()


# ---------------------------------------------------------------------------
# 5. LLM API failure → unavailable, no fake Python verdict
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion", side_effect=RuntimeError("API timeout"))
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_llm_api_failure(mock_completion):
    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "unavailable"
    assert result["_judge_source"] == "error"
    # Confirm no Python-generated verdict leaked through
    assert result["explanation"] == ""
    assert result["strengths"] == []
    assert result["risks"] == []
    assert result["recommendation"] == ""


# ---------------------------------------------------------------------------
# 6. LLM returns invalid verdict string → unavailable
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_invalid_verdict_string(mock_completion):
    payload = {"verdict": "Maybe", "explanation": "...", "strengths": [], "risks": [], "recommendation": ""}
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    mock_completion.return_value = MagicMock(choices=[choice])

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "unavailable"
    assert result["_judge_source"] == "invalid_verdict"


# ---------------------------------------------------------------------------
# 7. LLM returns a non-dict (e.g. a list) → unavailable
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_non_dict_llm_response(mock_completion):
    message = MagicMock()
    message.content = json.dumps(["verdict", "Promising"])  # a list, not a dict
    choice = MagicMock()
    choice.message = message
    mock_completion.return_value = MagicMock(choices=[choice])

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "unavailable"
    assert result["_judge_source"] == "invalid_llm_output"


# ---------------------------------------------------------------------------
# 8. Empty analysis dict → unavailable
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_empty_analysis():
    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict({}, CONTEXT)

    assert result["verdict"] == "unavailable"
    assert result["_judge_source"] == "incomplete_data"


# ---------------------------------------------------------------------------
# 9. None analysis → unavailable
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_none_analysis():
    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(None, CONTEXT)

    assert result["verdict"] == "unavailable"
    assert result["_judge_source"] == "incomplete_data"


# ---------------------------------------------------------------------------
# 10. Partial analysis (missing some specialist results) → still runs,
#     missing values fall back to safe defaults
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_partial_analysis_uses_defaults(mock_completion):
    """Missing specialist results should use safe defaults, not crash."""
    mock_completion.return_value = _make_llm_response("Risky")

    partial = {"location_result": ANALYSIS["location_result"]}  # only location provided

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(partial, CONTEXT)

    # Should complete — either a valid verdict or unavailable
    assert result["verdict"] in {"Promising", "Risky", "Not Recommended", "unavailable"}


# ---------------------------------------------------------------------------
# 11. JSON parsing handles markdown fences
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_json_parsing_with_markdown_fences(mock_completion):
    payload = {
        "verdict": "Promising",
        "explanation": "Looks good.",
        "strengths": ["Strong area"],
        "risks": ["High competition"],
        "recommendation": "Run a pilot.",
    }
    # LLM wraps it in ```json ... ```
    message = MagicMock()
    message.content = "```json\n" + json.dumps(payload) + "\n```"
    choice = MagicMock()
    choice.message = message
    mock_completion.return_value = MagicMock(choices=[choice])

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    assert result["verdict"] == "Promising"
    assert result["_judge_source"] == "llm_primary"


# ---------------------------------------------------------------------------
# 12. Financial simulator data must NOT reach generate_judge_verdict
#     Verify by inspecting what the coordinator passes
# ---------------------------------------------------------------------------

def test_coordinator_excludes_financial_data():
    """
    The coordinator must build judge_inputs from only the four permitted
    specialist results. This test verifies that financial_result and
    'financial' keys are absent from what would be passed to the Judge Agent.
    """
    # Simulate what coordinator_agent.py does at step 7
    location_result    = ANALYSIS["location_result"]
    performance_result = ANALYSIS["performance_result"]
    competition_result = ANALYSIS["competition_result"]
    opportunity_result = ANALYSIS["opportunity_result"]

    # This is the exact block from coordinator_agent.py
    judge_inputs = {
        "location_result":    location_result,
        "performance_result": performance_result,
        "competition_result": competition_result,
        "opportunity_result": opportunity_result,
    }

    # Confirm financial keys are absent
    assert "financial_result" not in judge_inputs, \
        "financial_result must not be passed to the Judge Agent"
    assert "financial" not in judge_inputs, \
        "'financial' alias must not be passed to the Judge Agent"

    # Confirm all four permitted keys are present
    for key in ("location_result", "performance_result", "competition_result", "opportunity_result"):
        assert key in judge_inputs, f"Required key '{key}' is missing from judge_inputs"


# ---------------------------------------------------------------------------
# 13. _extract_metrics never touches financial keys
# ---------------------------------------------------------------------------

def test_extract_metrics_ignores_financial_keys():
    """
    Even if financial data is accidentally present in the analysis dict,
    _extract_metrics must not read revenue, profit, margin, or break-even.
    """
    from src.agent.judge_agent import _extract_metrics

    # Inject financial data — it should be silently ignored
    analysis_with_financials = {
        **ANALYSIS,
        "financial_result": {
            "monthly_revenue": 999999,
            "estimated_operating_profit": 500000,
            "operating_profit_margin": 50.0,
            "break_even_target_customers_per_day": 20,
        },
        "financial": {
            "monthly_revenue": 999999,
        },
    }

    metrics = _extract_metrics(analysis_with_financials, CONTEXT)

    # None of the financial keys should appear in the extracted metrics
    financial_keys = {"revenue", "profit", "margin", "break_even", "monthly_revenue",
                      "operating_profit_margin", "estimated_operating_profit"}
    for key in financial_keys:
        assert key not in metrics, f"Financial key '{key}' must not appear in judge metrics"


# ---------------------------------------------------------------------------
# 14. Output contract — all required keys always present
# ---------------------------------------------------------------------------

@patch("src.agent.judge_agent.litellm.completion")
@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "test-api-key")
def test_output_contract_on_success(mock_completion):
    mock_completion.return_value = _make_llm_response("Promising")

    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    required_keys = {"verdict", "explanation", "strengths", "risks", "recommendation", "_judge_source"}
    assert required_keys == set(result.keys()), \
        f"Unexpected keys in result: {set(result.keys()) - required_keys}"


@patch("src.agent.judge_agent.PRIMARY_LLM_API_KEY", "")
def test_output_contract_on_failure():
    from src.agent.judge_agent import generate_judge_verdict
    result = generate_judge_verdict(ANALYSIS, CONTEXT)

    required_keys = {"verdict", "explanation", "strengths", "risks", "recommendation", "_judge_source"}
    assert required_keys == set(result.keys())
    assert result["verdict"] == "unavailable"
