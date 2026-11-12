"""
Deterministic scenario-comparison module for BizAdvisor.

Separates two independent concerns:
1. Financial What-If: Compares cost/revenue assumptions using simulate_financials().
   Does not invoke the ML model or Google Places API.
2. ML What-If: Compares operational features using predict_business_performance().
   Does not retrain the model or invoke Google Places API.

Note: Outputs are directional scenario estimates based on input assumptions,
not guaranteed future business outcomes.
"""

from __future__ import annotations

from src.finance.simulator import simulate_financials
from src.ml.predictor import predict_business_performance


def _safe_pct_change(baseline_value: float, scenario_value: float) -> float | None:
    """
    Calculate percentage change from baseline to scenario.

    Returns None when the baseline is zero (division undefined),
    and 0.0 when both values are zero.
    """
    if baseline_value == 0:
        if scenario_value == 0:
            return 0.0
        return None
    return ((scenario_value - baseline_value) / abs(baseline_value)) * 100


def _build_change_entry(baseline_value: float | None, scenario_value: float | None) -> dict:
    """Build a comparison entry (absolute and percentage change) for a numeric metric."""
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


def compare_financial_scenarios(
    baseline_inputs: dict,
    scenario_inputs: dict,
) -> dict:
    """
    Compare baseline and scenario financial assumptions using simulate_financials().

    Does not call the ML predictor or Google Places API.
    """
    baseline_fin = {k: v for k, v in baseline_inputs.items() if k in FINANCIAL_KEYS}
    scenario_fin = {k: v for k, v in scenario_inputs.items() if k in FINANCIAL_KEYS}

    baseline_result = simulate_financials(**baseline_fin)
    scenario_result = simulate_financials(**scenario_fin)

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

    has_changes = any(
        v.get("absolute") is not None and abs(v.get("absolute")) > 1e-4
        for v in changes.values()
    )

    return {
        "baseline": baseline_result,
        "scenario": scenario_result,
        "changes": changes,
        "has_financial_changes": has_changes,
    }


def compare_ml_scenarios(
    baseline_ml_inputs: dict,
    scenario_ml_inputs: dict,
    include_shap: bool = False,
) -> dict:
    """
    Compare baseline and scenario ML inputs using the existing Random Forest model.

    The model is not retrained, and no Google Places API calls are made.

    Parameters:
        include_shap: Deprecated parameter retained for backward compatibility.
    """
    baseline_pred = predict_business_performance(**baseline_ml_inputs)
    scenario_pred = predict_business_performance(**scenario_ml_inputs)

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
        },
        "scenario": {
            "prediction": scenario_pred["prediction"],
            "probabilities": scenario_pred["probabilities"],
        },
        "changes": {
            "prediction_changed": (
                baseline_pred["prediction"] != scenario_pred["prediction"]
            ),
            "probability_changes": probability_changes,
        },
    }


def describe_financial_changes(comparison: dict) -> list[str]:
    """Produce factual plain-language statements describing calculated financial changes."""
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
