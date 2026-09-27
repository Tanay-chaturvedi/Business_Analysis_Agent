from google.adk.agents import Agent
from google.adk.tools import ToolContext
from src.analysis.opportunity import analyze_business_opportunity


# The exact set of keys that competition_summary MUST contain.
_REQUIRED_COMPETITION_KEYS = {
    "competitor_count_retrieved",
    "avg_competitor_rating",
    "median_competitor_rating",
    "avg_competitor_reviews",
    "median_competitor_reviews",
    "high_rating_competitors",
    "high_review_competitors",
}


def opportunity_analysis_tool(
    probabilities: list | dict = None,
    model_classes: list = None,
    competition_summary: dict = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Calculate the business opportunity score using
    ML probabilities and competition summary.

    Raises ValueError if required Performance Agent output
    (probabilities / model_classes) is missing, or if
    competition_summary is missing or incomplete.
    """
    # 1. Pull from ToolContext state when arguments are omitted
    if tool_context and hasattr(tool_context, "state"):
        if (probabilities is None or (isinstance(probabilities, list) and len(probabilities) == 0)):
            if "performance_result" in tool_context.state:
                perf = tool_context.state["performance_result"]
                if isinstance(perf, dict) and "probabilities" in perf:
                    prob_dict = perf["probabilities"]
                    model_classes = list(prob_dict.keys())
                    probabilities = list(prob_dict.values())

        if competition_summary is None or (isinstance(competition_summary, dict) and len(competition_summary) == 0):
            if "competition_result" in tool_context.state:
                competition_summary = tool_context.state["competition_result"]

    # 2. Validate Performance Agent data — never fabricate
    if isinstance(probabilities, dict):
        model_classes = list(probabilities.keys())
        probabilities = [float(v) for v in probabilities.values()]
    elif isinstance(probabilities, list) and len(probabilities) > 0:
        probabilities = [float(v) for v in probabilities]
    else:
        raise ValueError(
            "Performance Agent output is required: 'probabilities' is missing or empty. "
            "Run the Performance Agent first and pass its actual probabilities."
        )

    if model_classes is None or len(model_classes) == 0:
        raise ValueError(
            "Performance Agent output is required: 'model_classes' is missing or empty. "
            "Run the Performance Agent first and pass its actual model class labels."
        )

    if len(probabilities) != len(model_classes):
        raise ValueError(
            f"'probabilities' length ({len(probabilities)}) does not match "
            f"'model_classes' length ({len(model_classes)}). "
            "Both must come from the same Performance Agent output."
        )

    # 3. Validate competition_summary — never rename keys or guess values
    if competition_summary is None or not isinstance(competition_summary, dict):
        raise ValueError(
            "Competition Agent output is required: 'competition_summary' is missing. "
            "Run the Competition Agent first and pass its actual competition_summary."
        )

    missing_keys = _REQUIRED_COMPETITION_KEYS - set(competition_summary.keys())
    if missing_keys:
        raise ValueError(
            f"competition_summary is missing required keys: {sorted(missing_keys)}. "
            "Do not rename keys or substitute alternative values. "
            "Pass the exact competition_summary returned by the Competition Agent."
        )

    # 4. Compute the opportunity score using validated, real data
    result = analyze_business_opportunity(
        probabilities=probabilities,
        model_classes=model_classes,
        competition_summary=competition_summary
    )

    if tool_context and hasattr(tool_context, "state"):
        tool_context.state["opportunity_result"] = result

    return result


opportunity_agent = Agent(
    name="opportunity_agent",
    model="gemini-3.6-flash",

    description=(
        "Specialized agent responsible for evaluating "
        "business opportunity using historical ML performance "
        "and competition analysis."
    ),

    instruction="""
You are the Opportunity Agent.

Your ONLY responsibility is business opportunity analysis.

You MUST use opportunity_analysis_tool.

The Python tool is the SINGLE SOURCE OF TRUTH for all calculations.

IMPORTANT INPUT FORMAT:

The tool accepts:

1. probabilities
   - A list of numerical ML probabilities or a dictionary mapping class names to probabilities.

2. model_classes
   - A list containing the class names corresponding to the probabilities (e.g. ["High", "Low", "Medium"]).

3. competition_summary
   - A dictionary with EXACTLY these keys:

     {
         "competitor_count_retrieved": number,
         "avg_competitor_rating": number,
         "median_competitor_rating": number,
         "avg_competitor_reviews": number,
         "median_competitor_reviews": number,
         "high_rating_competitors": number,
         "high_review_competitors": number
     }

When receiving competition data from the Competition Agent,
pass the exact competition_summary dictionary — do NOT rename
keys or substitute alternative values.

When receiving performance data from the Performance Agent,
use its probabilities and model_classes exactly as returned.

The tool will raise a clear error if any required input is
missing. Do NOT invent or fabricate replacement values.

Your ONLY task is to calculate and report the opportunity
assessment.

You must:

1. Use opportunity_analysis_tool.
2. Treat the tool output as the SINGLE SOURCE OF TRUTH.
3. Report numerical scores exactly as returned.
4. Do NOT recalculate scores.
5. Do NOT modify scores.
6. Do NOT invent probabilities or competition values.
7. Do NOT change classifications.
8. Preserve signals exactly as returned.

Do NOT perform:

- Google Places searches
- competitor discovery
- historical location lookup
- Random Forest prediction

Those responsibilities belong to other agents.

Do NOT claim that the opportunity score guarantees
business success, revenue, or profitability.

The tool returns:

- opportunity_score
- historical_performance
- competition_strength

Each contains:

- score
- signal

Report these clearly.
""",

    tools=[opportunity_analysis_tool]
)
