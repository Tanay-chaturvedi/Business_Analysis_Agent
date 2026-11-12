from google.adk.agents import Agent
from src.agent.llm_config import PRIMARY_MODEL_NAME

from src.ml.predictor import predict_business_performance
from src.analysis.location_context import get_location_context


def performance_analysis_tool(
    online_order: int,
    book_table: int,
    approx_costfor_two_people: float,
    cost_band: str,
    location: str,
    primary_cuisine: str,
    primary_rest_type: str,
    cuisine_count: int = 2,
    historical_restaurant_count: int = 0,
    location_median_cost: float = 0.0,
    location_online_order_rate: float = 0.0,
    location_book_table_rate: float = 0.0,
    location_cuisine_diversity: int = 0,
    location_business_type_diversity: int = 0,
    progress_callback = None
) -> dict:
    """
    Predict historical performance class and probabilities for a proposed business
    using the Random Forest machine learning model.
    """

    # If historical location context metrics were not provided, retrieve them
    if (
        historical_restaurant_count == 0
        or location_median_cost == 0.0
    ):
        loc_ctx = get_location_context(location)

        if loc_ctx and loc_ctx.get("found", False):
            historical_restaurant_count = loc_ctx.get("historical_restaurant_count", historical_restaurant_count)
            location_median_cost = loc_ctx.get("location_median_cost", location_median_cost)
            location_online_order_rate = loc_ctx.get("location_online_order_rate", location_online_order_rate)
            location_book_table_rate = loc_ctx.get("location_book_table_rate", location_book_table_rate)
            location_cuisine_diversity = loc_ctx.get("location_cuisine_diversity", location_cuisine_diversity)
            location_business_type_diversity = loc_ctx.get("location_business_type_diversity", location_business_type_diversity)

    if progress_callback:
        progress_callback("performance", "started", "Running Random Forest prediction...")

    pred_res = predict_business_performance(
        online_order=online_order,
        book_table=book_table,
        approx_costfor_two_people=approx_costfor_two_people,
        cost_band=cost_band,
        location=location,
        primary_cuisine=primary_cuisine,
        cuisine_count=cuisine_count,
        primary_rest_type=primary_rest_type,
        historical_restaurant_count=historical_restaurant_count,
        location_median_cost=location_median_cost,
        location_online_order_rate=location_online_order_rate,
        location_book_table_rate=location_book_table_rate,
        location_cuisine_diversity=location_cuisine_diversity,
        location_business_type_diversity=location_business_type_diversity
    )

    if progress_callback:
        progress_callback("performance", "completed", "Prediction completed")

    result = {
        "prediction": pred_res["prediction"],
        "probabilities": pred_res["probabilities"],
    }

    return result


performance_agent = Agent(
    name="performance_agent",
    model=PRIMARY_MODEL_NAME,

    description=(
        "Specialized agent responsible for predicting "
        "historical restaurant performance using the "
        "Random Forest machine learning model."
    ),

    instruction="""
You are the Performance Agent.

Your ONLY responsibility is historical restaurant
performance prediction using the machine learning model.

You must:

1. Use performance_analysis_tool to obtain the ML prediction and class probabilities.

2. Treat the output of performance_analysis_tool as the
   SINGLE SOURCE OF TRUTH.

3. Report the prediction exactly as returned by the tool.

4. Report all probability values exactly as returned by
   the tool.

5. Do NOT recalculate, modify, estimate, or invent
   probabilities or predictions.

6. Do NOT change the predicted performance class.

7. Do NOT claim that the prediction represents actual
   profit, revenue, or guaranteed business success.

8. Do NOT perform:
   - competitor analysis
   - Google Places searches
   - historical location analysis
   - opportunity scoring
   - profitability prediction

   These responsibilities belong to other specialized agents.

9. Keep the response focused on the ML prediction and probability distribution.

IMPORTANT:

The Python tool performs the actual machine learning prediction.
You are responsible only for presenting the result.
Never replace tool-derived values with your own calculations.
""",

    tools=[performance_analysis_tool]
)
