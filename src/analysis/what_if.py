"""
What-If Analysis — Phase 4
============================

Deterministic scenario-comparison module for the Business Analysis Agent.

PURPOSE
-------
Allows a business owner to compare a BASELINE business scenario against a
WHAT-IF scenario by answering questions such as:

    "What happens if I increase daily customers by 20?"
    "What happens if rent increases by ₹10,000?"
    "What happens if I switch to online ordering?"
    "What happens if I change the cuisine / business type?"

TWO INDEPENDENT CONCERNS
------------------------

1. FINANCIAL WHAT-IF
   Compares two sets of cost/revenue assumptions.
   Uses:  src.finance.simulator.simulate_financials()
   Does NOT call the ML model.
   Does NOT call Google Places.

2. ML WHAT-IF
   Compares two sets of ML-relevant business attributes.
   Uses:  src.ml.predictor.predict_business_performance()
   Optionally uses: src.ml.explainer.explain_business_prediction()
   Does NOT call Google Places.
   Does NOT retrain the model.
   Does NOT duplicate ML logic.

SCOPE RULES
-----------
Financial-only changes (rent, staff_cost, utilities, marketing,
other_expenses, food_cost_percent, customers_per_day, average_order_value)
NEVER trigger the ML predictor.

ML-relevant changes (online_order, book_table, approx_costfor_two_people,
cost_band, location, primary_cuisine, cuisine_count, primary_rest_type,
location-context features) are handled by compare_ml_scenarios().

IMPORTANT LIMITATIONS
---------------------
This module produces SCENARIO ESTIMATES, not future predictions.
Calculated effects report directional changes based on input assumptions.
Do NOT claim the output represents guaranteed future business outcomes.
"""

from __future__ import annotations

from src.finance.simulator import simulate_financials
from src.ml.predictor import predict_business_performance
from src.ml.explainer import explain_business_prediction


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _safe_pct_change(baseline_value: float, scenario_value: float) -> float | None:
    """
    Calculate percentage change from baseline to scenario.

    Returns None when the baseline is zero (division undefined).
    Returns 0.0 when both values are zero.

    Formula:
        ((scenario - baseline) / abs(baseline)) * 100
    """
    if baseline_value == 0:
        if scenario_value == 0:
            return 0.0
        return None  # division by zero — undefined
    return ((scenario_value - baseline_value) / abs(baseline_value)) * 100


def _build_change_entry(baseline_value: float | None, scenario_value: float | None) -> dict:
    """
    Build a single comparison entry for a numeric metric.

    Handles None break_even_customers_per_day values gracefully.
    """
    if baseline_value is None and scenario_value is None:
        return {"absolute": None, "percentage": None}
    if baseline_value is None:
        return {"absolute": None, "percentage": None}
    if scenario_value is None:
        return {"absolute": None, "percentage": None}

    absolute = round(scenario_value - baseline_value, 4)
    percentage = _safe_pct_change(baseline_value, scenario_value)
    return {
        "absolute": absolute,
        "percentage": round(percentage, 4) if percentage is not None else None,
    }


# ------------------------------------------------------------------
# Allowed keys for each domain
# ------------------------------------------------------------------

#: Keys accepted by simulate_financials()
FINANCIAL_KEYS: frozenset[str] = frozenset({
    "customers_per_day",
    "average_order_value",
    "rent",
    "staff_cost",
    "food_cost_percent",
    "utilities",
    "marketing",
    "other_expenses",
    "working_days",
})

#: Keys accepted by predict_business_performance() / explain_business_prediction()
ML_KEYS: frozenset[str] = frozenset({
    "online_order",
    "book_table",
    "approx_costfor_two_people",
    "cost_band",
    "location",
    "primary_cuisine",
    "cuisine_count",
    "primary_rest_type",
    "historical_restaurant_count",
    "location_median_cost",
    "location_online_order_rate",
    "location_book_table_rate",
    "location_cuisine_diversity",
    "location_business_type_diversity",
})


# ------------------------------------------------------------------
# Public API — Financial What-If
# ------------------------------------------------------------------

def compare_financial_scenarios(
    baseline_inputs: dict,
    scenario_inputs: dict,
) -> dict:
    """
    Compare two financial scenarios using the existing financial simulator.

    Both dictionaries must contain the keys accepted by simulate_financials().
    Unknown keys are silently ignored to allow callers to pass a superset dict.

    Parameters
    ----------
    baseline_inputs : dict
        Base-case financial assumptions. Required keys match simulate_financials().
    scenario_inputs : dict
        What-if financial assumptions. Required keys match simulate_financials().

    Returns
    -------
    dict
        {
            "baseline": <simulate_financials output>,
            "scenario": <simulate_financials output>,
            "changes": {
                "monthly_revenue":              {"absolute": float, "percentage": float|None},
                "monthly_expenses":             {"absolute": float, "percentage": float|None},
                "estimated_operating_profit":   {"absolute": float, "percentage": float|None},
                "operating_profit_margin":      {"absolute": float, "percentage": float|None},
                "break_even_customers_per_day": {"absolute": float|None, "percentage": float|None},
            }
        }

    Raises
    ------
    ValueError
        If either input set fails simulate_financials() validation.

    Notes
    -----
    This function does NOT call the ML predictor or Google Places API.
    """
    # Extract only the keys relevant to the financial simulator
    baseline_fin = {k: v for k, v in baseline_inputs.items() if k in FINANCIAL_KEYS}
    scenario_fin = {k: v for k, v in scenario_inputs.items() if k in FINANCIAL_KEYS}

    # Delegate to the existing financial simulator (validation happens there)
    baseline_result = simulate_financials(**baseline_fin)
    scenario_result = simulate_financials(**scenario_fin)

    # Keys to compare
    compare_keys = [
        "monthly_revenue",
        "monthly_expenses",
        "estimated_operating_profit",
        "operating_profit_margin",
        "break_even_customers_per_day",
    ]

    changes = {}
    for key in compare_keys:
        changes[key] = _build_change_entry(
            baseline_result.get(key),
            scenario_result.get(key),
        )

    return {
        "baseline": baseline_result,
        "scenario": scenario_result,
        "changes": changes,
    }


# ------------------------------------------------------------------
# Public API — ML What-If
# ------------------------------------------------------------------

def compare_ml_scenarios(
    baseline_ml_inputs: dict,
    scenario_ml_inputs: dict,
    include_shap: bool = False,
) -> dict:
    """
    Compare two sets of ML-relevant business inputs using the existing
    Random Forest model.

    Parameters
    ----------
    baseline_ml_inputs : dict
        Base-case ML inputs. Must contain all keys required by
        predict_business_performance().
    scenario_ml_inputs : dict
        What-if ML inputs. Must contain all keys required by
        predict_business_performance().
    include_shap : bool, optional
        If True, also runs explain_business_prediction() for both scenarios.
        Default is False.

    Returns
    -------
    dict
        {
            "baseline": {
                "prediction":    str,
                "probabilities": dict,
                "shap":          dict | None   (None unless include_shap=True)
            },
            "scenario": {
                "prediction":    str,
                "probabilities": dict,
                "shap":          dict | None
            },
            "changes": {
                "prediction_changed": bool,
                "probability_changes": {
                    "<class>": {"absolute": float, "percentage": float|None},
                    ...
                }
            }
        }

    Raises
    ------
    KeyError
        If a required ML input key is missing from either dict.

    Notes
    -----
    This function does NOT call Google Places.
    The model is NOT retrained.
    Probabilities come directly from the existing Random Forest model.
    SHAP values come directly from the existing TreeExplainer.
    """
    # Run baseline ML prediction
    baseline_pred = predict_business_performance(**baseline_ml_inputs)

    # Run scenario ML prediction
    scenario_pred = predict_business_performance(**scenario_ml_inputs)

    # Optional SHAP
    baseline_shap = None
    scenario_shap = None
    if include_shap:
        baseline_shap = explain_business_prediction(**baseline_ml_inputs)
        scenario_shap = explain_business_prediction(**scenario_ml_inputs)

    # Build probability-level changes
    all_classes = set(baseline_pred["probabilities"]) | set(scenario_pred["probabilities"])
    probability_changes = {}
    for cls in sorted(all_classes):
        b_prob = baseline_pred["probabilities"].get(cls, 0.0)
        s_prob = scenario_pred["probabilities"].get(cls, 0.0)
        probability_changes[cls] = _build_change_entry(b_prob, s_prob)

    return {
        "baseline": {
            "prediction": baseline_pred["prediction"],
            "probabilities": baseline_pred["probabilities"],
            "shap": baseline_shap,
        },
        "scenario": {
            "prediction": scenario_pred["prediction"],
            "probabilities": scenario_pred["probabilities"],
            "shap": scenario_shap,
        },
        "changes": {
            "prediction_changed": (
                baseline_pred["prediction"] != scenario_pred["prediction"]
            ),
            "probability_changes": probability_changes,
        },
    }


# ------------------------------------------------------------------
# Public API — Interpretation layer (factual, no subjective claims)
# ------------------------------------------------------------------

def describe_financial_changes(comparison: dict) -> list[str]:
    """
    Produce a list of factual plain-language statements about the financial
    comparison result.

    This function reports CALCULATED EFFECTS only.
    It does NOT make subjective business recommendations.

    Parameters
    ----------
    comparison : dict
        Output of compare_financial_scenarios().

    Returns
    -------
    list[str]
        Ordered list of factual change statements. Empty list if no changes.
    """
    changes = comparison.get("changes", {})
    statements = []

    def _fmt(value: float | None, unit: str = "₹") -> str:
        if value is None:
            return "N/A"
        sign = "+" if value >= 0 else ""
        if unit == "₹":
            return f"{sign}₹{abs(value):,.2f}" if value >= 0 else f"-₹{abs(value):,.2f}"
        if unit == "%":
            return f"{sign}{value:.4f}%"
        return f"{sign}{value:.4f}"

    metric_labels = {
        "monthly_revenue":            "Monthly revenue",
        "monthly_expenses":           "Monthly expenses",
        "estimated_operating_profit": "Estimated operating profit",
        "operating_profit_margin":    "Operating profit margin",
        "break_even_customers_per_day": "Break-even customers/day",
    }

    for key, label in metric_labels.items():
        entry = changes.get(key, {})
        absolute = entry.get("absolute")
        percentage = entry.get("percentage")
        if absolute is None:
            continue
        if absolute == 0:
            continue

        if key == "operating_profit_margin":
            stmt = f"{label} changed by {_fmt(absolute, '%')}."
        elif key == "break_even_customers_per_day":
            sign = "+" if absolute >= 0 else ""
            stmt = (
                f"{label} changed by {sign}{absolute:.4f} customers/day"
                + (f" ({_fmt(percentage, '%')})" if percentage is not None else "")
                + "."
            )
        else:
            stmt = (
                f"{label} changed by {_fmt(absolute, '₹')}"
                + (f" ({_fmt(percentage, '%')})" if percentage is not None else "")
                + "."
            )
        statements.append(stmt)

    return statements
