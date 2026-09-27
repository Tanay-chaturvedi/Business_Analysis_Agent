import os
import joblib
import numpy as np
import pandas as pd
import shap

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


def clean_feature_name(raw_name: str) -> str:
    """
    Format raw preprocessor feature names to be human readable.
    """
    name = raw_name.replace("categorical__", "").replace("numerical__", "")
    return name


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

    input_data = pd.DataFrame([{
        "online_order": online_order,
        "book_table": book_table,
        "approx_costfor_two_people": approx_costfor_two_people,
        "log_cost": log_cost,
        "cost_band": cost_band,
        "location": location,
        "primary_cuisine": primary_cuisine,
        "cuisine_count": cuisine_count,
        "primary_rest_type": primary_rest_type,
        "historical_restaurant_count": historical_restaurant_count,
        "location_median_cost": location_median_cost,
        "location_online_order_rate": location_online_order_rate,
        "location_book_table_rate": location_book_table_rate,
        "location_cuisine_diversity": location_cuisine_diversity,
        "location_business_type_diversity": location_business_type_diversity
    }])

    encoded_data = preprocessor.transform(input_data)
    prediction = rf_model.predict(encoded_data)[0]

    classes = list(rf_model.classes_)
    pred_idx = classes.index(prediction)

    shap_vals = explainer.shap_values(encoded_data)

    if isinstance(shap_vals, np.ndarray) and len(shap_vals.shape) == 3:
        vals = shap_vals[0, :, pred_idx]
    elif isinstance(shap_vals, list):
        vals = shap_vals[pred_idx][0, :]
    else:
        vals = shap_vals[0, :]

    feature_names = preprocessor.get_feature_names_out()

    top_indices = np.argsort(np.abs(vals))[::-1][:top_n]

    top_features = []
    for idx in top_indices:
        raw_name = feature_names[idx]
        contrib = float(vals[idx])
        clean_name = clean_feature_name(raw_name)
        top_features.append({
            "feature": clean_name,
            "contribution": round(contrib, 4),
            "direction": "positive" if contrib >= 0 else "negative"
        })

    return {
        "prediction": str(prediction),
        "top_features": top_features
    }
