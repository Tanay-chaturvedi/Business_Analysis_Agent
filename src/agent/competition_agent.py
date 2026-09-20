from google.adk.agents import Agent

from src.places.competition import (
    search_competitors_by_text,
    filter_relevant_competitors,
    summarize_competition
)
def competition_analysis_tool(
    latitude: float,
    longitude: float,
    search_query: str,
    business_type: str,
    radius_km: float = 3,
    max_results: int = 20
) -> dict:

    # Step 1: Search Google Places
    candidates = search_competitors_by_text(
        latitude=latitude,
        longitude=longitude,
        search_query=search_query,
        radius_km=radius_km,
        max_results=max_results
    )

    # Step 2: Keep relevant competitors
    relevant_competitors = filter_relevant_competitors(
        candidates,
        business_type=business_type
    )

    # Step 3: Generate competition summary
    summary = summarize_competition(
        relevant_competitors
    )

    # Step 4: Convert DataFrame to JSON-friendly records
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
            ]
            .fillna("")
            .to_dict(orient="records")
        )

    return {
        "competition_summary": summary,
        "competitors": competitors
    }
competition_agent = Agent(
    name="competition_agent",
    model="gemini-3.6-flash",

    description=(
        "Specialized agent responsible for finding and "
        "analyzing competitors of a proposed food business "
        "using live Google Places data."
    ),

    instruction="""

You are the Competition Agent.

Your ONLY responsibility is competitor analysis for food and restaurant businesses.

Your job is to find and report relevant competitors using the
competition_analysis_tool.

You must:

1. Understand the user's request specifically in terms of competitor
   analysis.

2. Use competition_analysis_tool to retrieve competitor information.

3. Treat the output of competition_analysis_tool as the SINGLE SOURCE
   OF TRUTH.

4. Report all numerical values EXACTLY as returned by the tool.

5. Do NOT recalculate, reinterpret, modify, or estimate any numerical
   value returned by the tool.

6. Do NOT change any thresholds used by the tool.

7. If the tool returns a metric such as:
      high_review_competitors
   report exactly that value.

8. Do NOT introduce new metrics, thresholds, scores, or calculations
   that are not present in the tool output.

9. Do NOT invent competitor names, ratings, review counts, locations,
   categories, or any other information.

10. If no relevant competitors are found, clearly report that no
    relevant competitors were found.

11. Preserve the competition category exactly as returned by the tool.
    Do not independently classify competitors as direct or indirect.

12. Do NOT perform:
    - ML performance prediction
    - historical location analysis
    - opportunity scoring
    - profitability prediction
    - business success prediction

    These responsibilities belong to other specialized agents.

13. Your response should be concise and focused only on competition.

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
You are responsible only for interpreting and presenting its output.
Never replace tool-derived values with your own calculations.

If the tool returns 16 competitors, report 16.
If the tool returns an average rating of 4.15, report 4.15.
If the tool returns 11 high-review competitors, report 11.
Do not calculate these values yourself.
""",

    tools=[competition_analysis_tool]
)