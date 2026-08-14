import os
import joblib
import numpy as np
import pandas as pd


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


# Load trained model and preprocessor
rf_model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)


def predict_business_performance(
    online_order,
    book_table,
    approx_costfor_two_people,
    cost_band,
    location,
    primary_cuisine,
    cuisine_count,
    primary_rest_type,
    historical_restaurant_count,
    location_median_cost,
    location_online_order_rate,
    location_book_table_rate,
    location_cuisine_diversity,
    location_business_type_diversity
):
    """
    Predict historical performance class for a proposed business.
    """

    log_cost = np.log1p(
        approx_costfor_two_people
    )

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

    # Apply the same preprocessing used during training
    encoded_data = preprocessor.transform(input_data)

    # Prediction
    prediction = rf_model.predict(encoded_data)[0]

    # Probabilities
    probabilities = rf_model.predict_proba(
        encoded_data
    )[0]

    probability_dict = {
        class_name: round(float(probability), 4)
        for class_name, probability in zip(
            rf_model.classes_,
            probabilities
        )
    }

    return {
        "prediction": prediction,
        "probabilities": probability_dict
    }