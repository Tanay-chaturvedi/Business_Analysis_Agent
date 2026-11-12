from google.adk.agents import Agent

from src.agent.llm_config import PRIMARY_MODEL_NAME
from src.analysis.opportunity import analyze_business_opportunity


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
    competition_summary: dict = None
) -> dict:
    """
    Calculate business opportunity using ML predictions
    and competition analysis.
    """

    # Validate and normalize ML probabilities
    if isinstance(probabilities, dict):
        model_classes = list(probabilities.keys())
        probabilities = [float(v) for v in probabilities.values()]

    elif isinstance(probabilities, list) and probabilities:
        probabilities = [float(v) for v in probabilities]

    else:
        raise ValueError(
            "Performance Agent probabilities are missing. "
            "Run the Performance Agent first."
        )

    if not model_classes:
        raise ValueError(
            "Performance Agent model_classes are missing. "
            "Provide the actual model class labels."
        )

    if len(probabilities) != len(model_classes):
        raise ValueError(
            "Probabilities and model_classes must have matching lengths."
        )

    # Validate competition summary
    if not isinstance(competition_summary, dict):
        raise ValueError(
            "Competition Agent competition_summary is missing. "
            "Run the Competition Agent first."
        )

    missing_keys = _REQUIRED_COMPETITION_KEYS - competition_summary.keys()

    if missing_keys:
        raise ValueError(
            f"Competition summary is missing required keys: "
            f"{sorted(missing_keys)}"
        )

    # Calculate opportunity assessment
    result = analyze_business_opportunity(
        probabilities=probabilities,
        model_classes=model_classes,
        competition_summary=competition_summary
    )

    return result


opportunity_agent = Agent(
    name="opportunity_agent",
    model=PRIMARY_MODEL_NAME,

    description=(
        "Evaluates business opportunities using ML performance "
        "predictions and competitor analysis."
    ),

    instruction="""
You are the Opportunity Agent.

Your ONLY responsibility is business opportunity analysis.

You MUST use opportunity_analysis_tool.

INPUTS:
- probabilities and model_classes from the Performance Agent.
- competition_summary from the Competition Agent.

Use the exact values and keys returned by these agents.
Never invent, estimate, rename, or modify input values.

The tool validates all required inputs and calculates:
- opportunity_score
- historical_performance
- competition_strength

Each result contains a score and signal.

RULES:
1. Treat tool output as the single source of truth.
2. Report scores, classifications and signals exactly as returned.
3. Do not recalculate or modify any values.
4. Do not perform competitor searches, historical location
   analysis or ML predictions.
5. Do not claim that the opportunity score guarantees
   business success, revenue or profitability.

Present the three assessment results clearly and concisely.
""",

    tools=[opportunity_analysis_tool]
)
