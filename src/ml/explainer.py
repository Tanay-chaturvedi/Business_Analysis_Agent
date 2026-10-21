import os
import joblib
import numpy as np
import pandas as pd
import shap
from typing import Optional, List, Dict, Tuple, Any

# Project root
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "zomato_performance_model.pkl"
)

PREPROCESSOR_PATH = os.path.join(
    BASE_DIR,
    "models",
    "zomato_preprocessor.pkl"
)

_rf_model = None
_preprocessor = None
_explainer = None


def get_model_and_preprocessor():
    global _rf_model, _preprocessor, _explainer
    if _rf_model is None:
        _rf_model = joblib.load(MODEL_PATH)
    if _preprocessor is None:
        _preprocessor = joblib.load(PREPROCESSOR_PATH)
    if _explainer is None:
        _explainer = shap.TreeExplainer(_rf_model)
    return _rf_model, _preprocessor, _explainer


def get_feature_metadata(raw_name: str, input_dict: dict) -> tuple:
    """
    Returns (clean_feature, display_name, feature_value) for a given feature name and input dict.
    """
    clean_name = raw_name.replace("categorical__", "").replace("numerical__", "")

    if clean_name in ["book_table_1", "book_table_0", "book_table"]:
        display_name = "Table Booking"
        val = input_dict.get("book_table", 0)
        feature_value = "Yes" if val == 1 else "No"
        return clean_name, display_name, feature_value

    if clean_name in ["online_order_1", "online_order_0", "online_order"]:
        display_name = "Online Ordering"
        val = input_dict.get("online_order", 0)
        feature_value = "Yes" if val == 1 else "No"
        return clean_name, display_name, feature_value

    if clean_name == "approx_costfor_two_people":
        display_name = "Approx. Cost for Two"
        cost = input_dict.get("approx_costfor_two_people", 0)
        feature_value = f"₹{int(cost):,}" if cost else "N/A"
        return clean_name, display_name, feature_value

    if clean_name == "log_cost":
        display_name = "Cost (Model-transformed)"
        cost = input_dict.get("approx_costfor_two_people", 0)
        feature_value = f"₹{int(cost):,}" if cost else "N/A"
        return clean_name, display_name, feature_value

    if clean_name.startswith("cost_band"):
        if "_" in clean_name and not clean_name.endswith("cost_band"):
            suffix = clean_name.split("cost_band_")[-1]
            display_name = f"Cost Band: {suffix}"
        else:
            display_name = "Cost Band"
        feature_value = str(input_dict.get("cost_band", "N/A"))
        return clean_name, display_name, feature_value

    if clean_name.startswith("location") and clean_name not in [
        "location_median_cost", "location_online_order_rate", "location_book_table_rate",
        "location_cuisine_diversity", "location_business_type_diversity"
    ]:
        display_name = "Location"
        feature_value = str(input_dict.get("location", "N/A"))
        return clean_name, display_name, feature_value

    if clean_name.startswith("primary_cuisine"):
        if "_" in clean_name and clean_name != "primary_cuisine":
            suffix = clean_name.split("primary_cuisine_")[-1]
            display_name = f"Cuisine: {suffix}"
        else:
            display_name = "Primary Cuisine"
        feature_value = str(input_dict.get("primary_cuisine", "N/A"))
        return clean_name, display_name, feature_value

    if clean_name.startswith("primary_rest_type"):
        if "_" in clean_name and clean_name != "primary_rest_type":
            suffix = clean_name.split("primary_rest_type_")[-1]
            display_name = f"Rest Type: {suffix}"
        else:
            display_name = "Restaurant Type"
        feature_value = str(input_dict.get("primary_rest_type", "N/A"))
        return clean_name, display_name, feature_value

    if clean_name == "cuisine_count":
        display_name = "Cuisine Variety"
        feature_value = str(input_dict.get("cuisine_count", "N/A"))
        return clean_name, display_name, feature_value

    if clean_name == "historical_restaurant_count":
        display_name = "Location Density"
        count = input_dict.get("historical_restaurant_count", 0)
        feature_value = f"{count:,} rests" if count else "N/A"
        return clean_name, display_name, feature_value

    if clean_name == "location_median_cost":
        display_name = "Location Median Cost"
        cost = input_dict.get("location_median_cost", 0)
        feature_value = f"₹{int(cost):,}" if cost else "N/A"
        return clean_name, display_name, feature_value

    if clean_name == "location_online_order_rate":
        display_name = "Location Online Order Rate"
        rate = input_dict.get("location_online_order_rate", 0.0)
        feature_value = f"{rate * 100:.1f}%"
        return clean_name, display_name, feature_value

    if clean_name == "location_book_table_rate":
        display_name = "Location Table Booking Rate"
        rate = input_dict.get("location_book_table_rate", 0.0)
        feature_value = f"{rate * 100:.1f}%"
        return clean_name, display_name, feature_value

    if clean_name == "location_cuisine_diversity":
        display_name = "Location Cuisine Diversity"
        feature_value = str(input_dict.get("location_cuisine_diversity", "N/A"))
        return clean_name, display_name, feature_value

    if clean_name == "location_business_type_diversity":
        display_name = "Location Rest Type Diversity"
        feature_value = str(input_dict.get("location_business_type_diversity", "N/A"))
        return clean_name, display_name, feature_value

    display_name = clean_name.replace("_", " ").title()
    feature_value = str(input_dict.get(clean_name, "N/A"))
    return clean_name, display_name, feature_value


def explain_business_prediction(
    online_order: int,
    book_table: int,
    approx_costfor_two_people: float,
    cost_band: str,
    location: str,
    primary_cuisine: str,
    cuisine_count: int,
    primary_rest_type: str,
    historical_restaurant_count: int,
    location_median_cost: float,
    location_online_order_rate: float,
    location_book_table_rate: float,
    location_cuisine_diversity: int,
    location_business_type_diversity: int,
    top_n: int = 5
) -> dict:
    """
    Generate structured SHAP explanations for the Random Forest performance prediction.
    """
    rf_model, preprocessor, explainer = get_model_and_preprocessor()

    log_cost = np.log1p(approx_costfor_two_people)
    loc_clean = location.split(",")[0].strip() if isinstance(location, str) else location

    input_dict = {
        "online_order": online_order,
        "book_table": book_table,
        "approx_costfor_two_people": approx_costfor_two_people,
        "log_cost": log_cost,
        "cost_band": cost_band,
        "location": loc_clean,
        "primary_cuisine": primary_cuisine,
        "cuisine_count": cuisine_count,
        "primary_rest_type": primary_rest_type,
        "historical_restaurant_count": historical_restaurant_count,
        "location_median_cost": location_median_cost,
        "location_online_order_rate": location_online_order_rate,
        "location_book_table_rate": location_book_table_rate,
        "location_cuisine_diversity": location_cuisine_diversity,
        "location_business_type_diversity": location_business_type_diversity
    }

    input_data = pd.DataFrame([input_dict])

    encoded_data = preprocessor.transform(input_data)
    prediction = rf_model.predict(encoded_data)[0]

    classes = list(rf_model.classes_)
    pred_idx = classes.index(prediction)

    try:
        shap_vals = explainer.shap_values(encoded_data, check_additivity=False)
    except Exception:
        shap_vals = explainer.shap_values(encoded_data)

    if isinstance(shap_vals, np.ndarray) and len(shap_vals.shape) == 3:
        vals = shap_vals[0, :, pred_idx]
    elif isinstance(shap_vals, list):
        vals = shap_vals[pred_idx][0, :]
    else:
        vals = shap_vals[0, :]

    feature_names = preprocessor.get_feature_names_out()

    top_indices = np.argsort(np.abs(vals))[::-1]

    top_features = []
    seen_display_names = set()

    for idx in top_indices:
        raw_name = feature_names[idx]
        contrib = float(vals[idx])
        clean_name, display_name, feature_value = get_feature_metadata(raw_name, input_dict)

        if display_name in seen_display_names:
            continue

        seen_display_names.add(display_name)
        top_features.append({
            "feature": clean_name,
            "display_name": display_name,
            "feature_value": feature_value,
            "shap_value": round(contrib, 4),
            "contribution": round(contrib, 4),
            "direction": "positive" if contrib >= 0 else "negative"
        })

        if len(top_features) >= top_n:
            break

    return {
        "prediction": str(prediction),
        "top_features": top_features
    }


def get_canonical_feature_group(raw_name: str, input_dict: dict) -> tuple:
    clean = raw_name.replace("categorical__", "").replace("numerical__", "")
    if "cost" in clean:
        cost = input_dict.get("approx_cost_for_two") or input_dict.get("approx_costfor_two_people") or 0
        val = f"₹{int(cost):,}" if cost else "N/A"
        return "approx_cost_for_two", "Cost for Two", val
    if "online_order" in clean:
        val = "Yes" if input_dict.get("online_order") in (1, True, "1", "True") else "No"
        return "online_order", "Online Ordering", val
    if "book_table" in clean:
        val = "Yes" if input_dict.get("book_table") in (1, True, "1", "True") else "No"
        return "book_table", "Table Booking", val
    if "cuisine" in clean and "diversity" not in clean and "count" not in clean:
        val = str(input_dict.get("primary_cuisine", "N/A"))
        return "primary_cuisine", "Cuisine", val
    if "location" in clean and not any(m in clean for m in ["median", "order_rate", "table_rate", "diversity", "count"]):
        val = str(input_dict.get("location", "N/A"))
        return "location", "Location", val
    if "rest_type" in clean:
        val = str(input_dict.get("primary_rest_type") or input_dict.get("restaurant_type") or "N/A")
        return "primary_rest_type", "Restaurant Type", val

    clean_name, display_name, feature_value = get_feature_metadata(raw_name, input_dict)
    return clean_name, display_name, feature_value


def compare_shap_drivers(
    base_params: dict,
    scen_params: dict,
    loc_ctx: Optional[dict] = None,
    target_class: str = "High",
    top_n: int = 5
) -> dict:
    """
    Compare baseline vs scenario SHAP contributions specifically for the target_class ('High').
    Returns top model driver changes and a non-causal, dynamic narrative summary.
    """
    rf_model, preprocessor, explainer = get_model_and_preprocessor()
    classes = list(rf_model.classes_)

    target_idx = classes.index(target_class) if target_class in classes else 0

    ctx = loc_ctx or {}

    def build_input_dict(p: dict) -> dict:
        cost = float(p.get("approx_cost_for_two") or p.get("approx_costfor_two_people") or 800.0)
        loc = str(p.get("location", "Koramangala")).split(",")[0].strip()

        # Determine cost band if not present
        cost_band = p.get("cost_band")
        if not cost_band:
            if cost < 400: cost_band = "Low"
            elif cost < 1000: cost_band = "Medium"
            elif cost < 2000: cost_band = "Upper-Mid"
            else: cost_band = "High"

        oo = 1 if p.get("online_order") in (1, True, "1", "True") else 0
        bt = 1 if p.get("book_table") in (1, True, "1", "True") else 0

        return {
            "online_order": oo,
            "book_table": bt,
            "approx_costfor_two_people": cost,
            "log_cost": np.log1p(cost),
            "cost_band": cost_band,
            "location": loc,
            "primary_cuisine": str(p.get("primary_cuisine", "North Indian")),
            "cuisine_count": int(p.get("cuisine_count", 2)),
            "primary_rest_type": str(p.get("primary_rest_type") or p.get("restaurant_type") or "Casual Dining"),
            "historical_restaurant_count": int(ctx.get("historical_restaurant_count", 1000)),
            "location_median_cost": float(ctx.get("location_median_cost", 500.0)),
            "location_online_order_rate": float(ctx.get("location_online_order_rate", 0.60)),
            "location_book_table_rate": float(ctx.get("location_book_table_rate", 0.15)),
            "location_cuisine_diversity": int(ctx.get("location_cuisine_diversity", 10)),
            "location_business_type_diversity": int(ctx.get("location_business_type_diversity", 5))
        }

    b_dict = build_input_dict(base_params)
    s_dict = build_input_dict(scen_params)

    b_enc = preprocessor.transform(pd.DataFrame([b_dict]))
    s_enc = preprocessor.transform(pd.DataFrame([s_dict]))

    b_prob = round(float(rf_model.predict_proba(b_enc)[0][target_idx]) * 100, 1)
    s_prob = round(float(rf_model.predict_proba(s_enc)[0][target_idx]) * 100, 1)
    prob_delta = round(s_prob - b_prob, 1)

    try:
        b_shap = explainer.shap_values(b_enc, check_additivity=False)
        s_shap = explainer.shap_values(s_enc, check_additivity=False)
    except Exception:
        b_shap = explainer.shap_values(b_enc)
        s_shap = explainer.shap_values(s_enc)

    if isinstance(b_shap, np.ndarray) and len(b_shap.shape) == 3:
        b_vals = b_shap[0, :, target_idx]
        s_vals = s_shap[0, :, target_idx]
    elif isinstance(b_shap, list):
        b_vals = b_shap[target_idx][0, :]
        s_vals = s_shap[target_idx][0, :]
    else:
        b_vals = b_shap[0, :]
        s_vals = s_shap[0, :]

    feature_names = preprocessor.get_feature_names_out()

    grouped = {}
    for i, raw_name in enumerate(feature_names):
        field_key, display_name, b_val = get_canonical_feature_group(raw_name, b_dict)
        _, _, s_val = get_canonical_feature_group(raw_name, s_dict)

        b_contrib = float(b_vals[i])
        s_contrib = float(s_vals[i])

        if display_name not in grouped:
            grouped[display_name] = {
                "field": field_key,
                "display_name": display_name,
                "baseline_value": b_val,
                "scenario_value": s_val,
                "baseline_shap": 0.0,
                "scenario_shap": 0.0,
            }
        grouped[display_name]["baseline_shap"] += b_contrib
        grouped[display_name]["scenario_shap"] += s_contrib

    drivers = []
    for dname, data in grouped.items():
        b_s = round(data["baseline_shap"], 4)
        s_s = round(data["scenario_shap"], 4)
        delta = round(s_s - b_s, 4)
        drivers.append({
            "field": data["field"],
            "display_name": dname,
            "baseline_value": data["baseline_value"],
            "scenario_value": data["scenario_value"],
            "baseline_shap": b_s,
            "scenario_shap": s_s,
            "shap_delta": delta,
            "abs_delta": abs(delta),
            "direction": "positive" if delta > 0 else ("negative" if delta < 0 else "neutral")
        })

    drivers.sort(key=lambda x: x["abs_delta"], reverse=True)
    top_drivers = drivers[:top_n]

    pos_drivers = [d for d in top_drivers if d["shap_delta"] > 0]
    neg_drivers = [d for d in top_drivers if d["shap_delta"] < 0]

    pos_names = ", ".join([d["display_name"] for d in pos_drivers])
    neg_names = ", ".join([d["display_name"] for d in neg_drivers])

    if prob_delta > 0:
        if pos_names:
            summary_text = (
                f"The model's predicted High-performance probability increased from {b_prob}% to {s_prob}% (+{prob_delta}% pts). "
                f"The largest positive changes in model contribution came from {pos_names}. Their SHAP contributions "
                f"became more supportive of the High-performance class in the scenario."
            )
        else:
            summary_text = (
                f"The model's predicted High-performance probability increased from {b_prob}% to {s_prob}% (+{prob_delta}% pts). "
                f"The feature contributions aligned more favorably with the High-performance prediction class."
            )
    elif prob_delta < 0:
        if neg_names:
            summary_text = (
                f"The model's predicted High-performance probability decreased from {b_prob}% to {s_prob}% ({prob_delta}% pts). "
                f"The largest negative changes in model contribution came from {neg_names}. Their SHAP contributions "
                f"became less supportive of the High-performance class in the scenario."
            )
        else:
            summary_text = (
                f"The model's predicted High-performance probability decreased from {b_prob}% to {s_prob}% ({prob_delta}% pts). "
                f"The feature contributions aligned less favorably with the High-performance prediction class."
            )
    else:
        summary_text = (
            f"The model's predicted High-performance probability remained unchanged at {b_prob}%. "
            f"SHAP feature contributions for the High-performance class were identical between baseline and scenario."
        )

    return {
        "model_driver_changes": top_drivers,
        "probability_explanation": {
            "baseline_high_probability": b_prob,
            "scenario_high_probability": s_prob,
            "delta_pct": prob_delta,
            "top_positive_drivers": [d["display_name"] for d in pos_drivers],
            "top_negative_drivers": [d["display_name"] for d in neg_drivers],
            "summary": summary_text
        }
    }
