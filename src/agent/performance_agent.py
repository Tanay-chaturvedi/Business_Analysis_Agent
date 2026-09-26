from google.adk.agents import Agent
from src.ml.predictor import predict_business_performance

def performance_analysis_tool(
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
    location_business_type_diversity: int
) -> dict:

    result = predict_business_performance(
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

    return result


performance_agent = Agent(
    name="performance_agent",
    model="gemini-3.6-flash",

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

1. Use performance_analysis_tool to obtain the ML prediction.

2. Treat the output of performance_analysis_tool as the
   SINGLE SOURCE OF TRUTH.

3. Report the prediction exactly as returned by the tool.

4. Report all probability values exactly as returned by
   the tool.

5. Do NOT recalculate, modify, estimate, or invent
   probabilities.

6. Do NOT change the predicted performance class.

7. Do NOT claim that the prediction represents actual
   profit, revenue, or guaranteed business success.

8. The model predicts historical performance class based
   on the features provided to it.

9. Do NOT perform:
   - competitor analysis
   - Google Places searches
   - historical location analysis
   - opportunity scoring
   - profitability prediction

   These responsibilities belong to other specialized agents.

10. Keep the response focused on the ML prediction.

IMPORTANT:

The Python tool performs the actual machine learning
prediction.

You are responsible only for presenting the result.

Never replace tool-derived values with your own calculations.

If the tool returns:

prediction = "High"

then report "High".

If the tool returns probabilities such as:

High = 0.52
Low = 0.18
Medium = 0.30

report those values exactly.
""",

    tools=[performance_analysis_tool]
)