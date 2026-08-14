from src.ml.predictor import predict_business_performance

from src.places.competition import (
    get_nearby_competitors,
    search_competitors_by_text,
    filter_relevant_competitors,
    summarize_competition
)

from src.analysis.location_context import (
    get_location_context
)

from src.analysis.opportunity import (
    analyze_business_opportunity
)


def analyze_business(
    location: str,
    latitude: float,
    longitude: float,
    business_type: str,
    primary_cuisine: str,
    cuisine_count: int,
    approx_costfor_two_people: float,
    cost_band: str,
    online_order: int,
    book_table: int,
    primary_rest_type: str,
    search_query: str = None,
    radius_km: float = 3,
    max_results: int = 20
) -> dict:
    """
    Complete business opportunity analysis.

    This function does NOT use Gemini.

    Pipeline:

        Location Context
              ↓
        ML Prediction
              ↓
        Google Places Text Search
              ↓
        Relevance Filtering
              ↓
        Competition Summary
              ↓
        Opportunity Analysis
              ↓
        Final Structured Result
    """

    # ========================================================
    # 1. LOCATION CONTEXT
    # ========================================================

    location_context = get_location_context(
        location
    )

    if not location_context.get("found"):
        raise ValueError(
            f"No historical location data found "
            f"for '{location}'."
        )

    historical_restaurant_count = (
        location_context[
            "historical_restaurant_count"
        ]
    )

    location_median_cost = (
        location_context[
            "location_median_cost"
        ]
    )

    location_online_order_rate = (
        location_context[
            "location_online_order_rate"
        ]
    )

    location_book_table_rate = (
        location_context[
            "location_book_table_rate"
        ]
    )

    location_cuisine_diversity = (
        location_context[
            "location_cuisine_diversity"
        ]
    )

    location_business_type_diversity = (
        location_context[
            "location_business_type_diversity"
        ]
    )

    # ========================================================
    # 2. MACHINE LEARNING PREDICTION
    # ========================================================

    ml_result = predict_business_performance(
        online_order=online_order,
        book_table=book_table,
        approx_costfor_two_people=(
            approx_costfor_two_people
        ),
        cost_band=cost_band,
        location=location,
        primary_cuisine=primary_cuisine,
        cuisine_count=cuisine_count,
        primary_rest_type=primary_rest_type,
        historical_restaurant_count=(
            historical_restaurant_count
        ),
        location_median_cost=(
            location_median_cost
        ),
        location_online_order_rate=(
            location_online_order_rate
        ),
        location_book_table_rate=(
            location_book_table_rate
        ),
        location_cuisine_diversity=(
            location_cuisine_diversity
        ),
        location_business_type_diversity=(
            location_business_type_diversity
        )
    )

    # ========================================================
    # 3. TEXT SEARCH
    # ========================================================

    if search_query is None:
        search_query = (
            f"{primary_cuisine} "
            f"{primary_rest_type} "
            f"in {location}"
        )

    text_candidates = search_competitors_by_text(
        latitude=latitude,
        longitude=longitude,
        search_query=search_query,
        radius_km=radius_km,
        max_results=max_results
    )

    # ========================================================
    # 4. RELEVANCE FILTERING
    # ========================================================

    relevant_competitors = (
        filter_relevant_competitors(
            text_candidates,
            business_type=business_type,
            include_indirect=True
        )
    )

    # ========================================================
    # 5. FALLBACK TO NEARBY SEARCH
    # ========================================================

    # If Text Search returned no relevant results,
    # use the original Nearby Search method.

    if relevant_competitors.empty:

        relevant_competitors = (
            get_nearby_competitors(
                latitude=latitude,
                longitude=longitude,
                business_type=business_type,
                radius_km=radius_km,
                max_results=max_results
            )
        )

        if not relevant_competitors.empty:

            relevant_competitors = (
                relevant_competitors.copy()
            )

            relevant_competitors[
                "competition_category"
            ] = "direct"

    # ========================================================
    # 6. COMPETITION SUMMARY
    # ========================================================

    competition_summary = (
        summarize_competition(
            relevant_competitors
        )
    )

    # Add direct/indirect counts
    if (
        not relevant_competitors.empty
        and "competition_category"
        in relevant_competitors.columns
    ):

        competition_summary[
            "direct_competitors"
        ] = int(
            (
                relevant_competitors[
                    "competition_category"
                ]
                == "direct"
            ).sum()
        )

        competition_summary[
            "indirect_competitors"
        ] = int(
            (
                relevant_competitors[
                    "competition_category"
                ]
                == "indirect"
            ).sum()
        )

    else:

        competition_summary[
            "direct_competitors"
        ] = 0

        competition_summary[
            "indirect_competitors"
        ] = 0

    # ========================================================
    # 7. OPPORTUNITY ANALYSIS
    # ========================================================

    probability_dict = ml_result[
        "probabilities"
    ]

    model_classes = [
        "High",
        "Low",
        "Medium"
    ]

    probabilities = [
        probability_dict["High"],
        probability_dict["Low"],
        probability_dict["Medium"]
    ]

    opportunity_result = (
        analyze_business_opportunity(
            probabilities,
            model_classes,
            competition_summary
        )
    )

    # ========================================================
    # 8. COMPETITOR RECORDS
    # ========================================================

    if relevant_competitors.empty:

        competitor_records = []

    else:

        competitor_columns = [
            "place_id",
            "name",
            "rating",
            "review_count",
            "latitude",
            "longitude"
        ]

        if "competition_category" in (
            relevant_competitors.columns
        ):
            competitor_columns.append(
                "competition_category"
            )

        competitor_records = (
            relevant_competitors[
                competitor_columns
            ]
            .fillna("")
            .to_dict(
                orient="records"
            )
        )

    # ========================================================
    # 9. FINAL STRUCTURED RESULT
    # ========================================================

    return {

        "business": {
            "location": location,

            "business_type": business_type,

            "primary_cuisine": primary_cuisine,

            "cuisine_count": cuisine_count,

            "approx_costfor_two_people": (
                approx_costfor_two_people
            ),

            "cost_band": cost_band,

            "online_order": online_order,

            "book_table": book_table,

            "primary_rest_type": (
                primary_rest_type
            ),

            "search_query": search_query
        },

        "location_context": (
            location_context
        ),

        "ml_prediction": ml_result,

        "competition": {
            "summary": (
                competition_summary
            ),

            "competitors": (
                competitor_records
            )
        },

        "opportunity_analysis": (
            opportunity_result
        )
    }