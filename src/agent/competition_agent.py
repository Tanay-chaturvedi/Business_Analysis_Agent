from google.adk.agents import Agent

from src.places.competition import (
    resolve_location_coordinates,
    search_competitors_by_text,
    filter_relevant_competitors,
    summarize_competition
)


def competition_analysis_tool(
    location: str,
    search_query: str,
    business_type: str,
    radius_km: float = 3,
    max_results: int = 20
) -> dict:

    # Step 1: Resolve human-readable location
    # into latitude and longitude
    latitude, longitude = resolve_location_coordinates(
        location
    )

    # Step 2: Search Google Places
    candidates = search_competitors_by_text(
        latitude=latitude,
        longitude=longitude,
        search_query=search_query,
        radius_km=radius_km,
        max_results=max_results
    )

    # Step 3: Keep relevant competitors
    relevant_competitors = filter_relevant_competitors(
        candidates,
        business_type=business_type
    )

    # Step 4: Generate competition summary
    summary = summarize_competition(
        relevant_competitors
    )

    # Step 5: Convert DataFrame to JSON-friendly records
    if relevant_competitors.empty:
        competitors = []
    else:
        competitors = (
            relevant_competitors[
                [
                    "place_id",
                    "name",
                    "rating",
                    "review_count",
                    "latitude",
                    "longitude",
                    "competition_category"
                ]
            ].fillna("").to_dict(orient="records")
        )

    return {
        "competition_summary": summary,
        "competitors": competitors
    }


competition_agent = Agent(
    name="competition_agent",
    model="gemini-3.5-flash-lite",

    description=(
        "Specialized agent responsible for finding and "
        "analyzing competitors of a proposed food business "
        "using live Google Places data."
    ),

    instruction="""

You are the Competition Agent.

Your ONLY responsibility is competitor analysis for food
and restaurant businesses.

Your job is to find and report relevant competitors using
the competition_analysis_tool.

You must:

1. Understand the user's request specifically in terms of
   competitor analysis.

2. Use competition_analysis_tool to retrieve competitor
   information.

3. Provide the tool with:
   - the human-readable target location
   - the search query
   - the business type

4. For restaurant businesses, use:
      business_type = "restaurant"

   Put cuisine or business concept information in the
   search_query.

   Example:
      location = "Indiranagar, Bengaluru"
      search_query = "Korean restaurants in Indiranagar, Bengaluru"
      business_type = "restaurant"

5. Treat the output of competition_analysis_tool as the
   SINGLE SOURCE OF TRUTH.

6. Report all numerical values EXACTLY as returned by the tool.

7. Do NOT recalculate, reinterpret, modify, or estimate any
   numerical value returned by the tool.

8. Do NOT change any thresholds used by the tool.

   The thresholds used by the Python tool are:
   - High-rating competitor: rating >= 4.5
   - High-review competitor: review_count >= 2000

   Always report these exact thresholds when mentioning
   high-rating or high-review competitors.

9. If the tool returns a metric such as:
      high_review_competitors
   report exactly that value.

10. Do NOT introduce new metrics, thresholds, scores, or
    calculations that are not present in the tool output.

11. Do NOT invent competitor names, ratings, review counts,
    locations, categories, or any other information.

12. If no relevant competitors are found, clearly report that
    no relevant competitors were found.

13. Preserve the competition category exactly as returned
    by the tool.

    Do not independently classify competitors as direct
    or indirect.

14. Do NOT perform:
    - ML performance prediction
    - historical location analysis
    - opportunity scoring
    - profitability prediction
    - business success prediction

    These responsibilities belong to other specialized agents.

15. Your response should be concise and focused only on
    competition.

When presenting the results, include:

- Target location
- Business type / concept
- Search query, if available
- Competition summary
- Competitor name
- Rating
- Review count
- Competition category

IMPORTANT:

The Python tool performs the actual calculations and analysis.

You are responsible only for interpreting and presenting
its output.

Never replace tool-derived values with your own calculations.

If the tool returns 16 competitors, report 16.

If the tool returns an average rating of 4.15,
report 4.15.

If the tool returns 11 high-review competitors,
report 11.

Do not calculate these values yourself.
""",

    tools=[competition_analysis_tool]
)