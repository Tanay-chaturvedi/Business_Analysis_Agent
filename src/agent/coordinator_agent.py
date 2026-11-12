from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from src.agent.llm_config import PRIMARY_MODEL_NAME
from src.agent.location_agent import (
    location_agent,
    location_analysis_tool,
)
from src.agent.performance_agent import (
    performance_agent,
    performance_analysis_tool,
)
from src.agent.competition_agent import (
    competition_agent,
    competition_analysis_tool,
)
from src.agent.opportunity_agent import (
    opportunity_agent,
    opportunity_analysis_tool,
)
from src.agent.insights_generator import generate_business_insights
from src.finance.simulator import simulate_financials


def validate_analysis_inputs(
    location=None,
    primary_cuisine=None,
    primary_rest_type=None,
    approx_costfor_two_people=None,
    online_order=None,
    book_table=None,
) -> dict:
    """Validate that all 6 required business parameters are provided."""
    required = {
        "location": location,
        "cuisine": primary_cuisine,
        "restaurant_type": primary_rest_type,
        "approx_costfor_two_people": approx_costfor_two_people,
        "has_online_order": online_order,
        "has_table_booking": book_table,
    }

    missing = [
        key
        for key, value in required.items()
        if value is None
        or str(value).strip().lower() in ("", "none", "missing", "unknown", "null")
    ]

    is_valid = len(missing) == 0
    return {
        "status": "valid" if is_valid else "needs_input",
        "is_valid": is_valid,
        "missing_inputs": missing,
    }


def run_full_business_analysis(
    location: str = None,
    search_query: str = None,
    online_order: int = None,
    book_table: int = None,
    approx_costfor_two_people: float = None,
    cost_band: str = "Medium",
    primary_cuisine: str = None,
    cuisine_count: int = 2,
    primary_rest_type: str = None,
    radius_km: float = 3,
    max_results: int = 20,
    customers_per_day: float = 100.0,
    average_order_value: float = None,
    rent: float = 60000.0,
    staff_cost: float = 50000.0,
    food_cost_percent: float = 30.0,
    utilities: float = 15000.0,
    marketing: float = 10000.0,
    other_expenses: float = 5000.0,
    working_days: float = 30.0,
    progress_callback=None,
) -> dict:
    """
    Execute complete end-to-end business analysis workflow across all specialist agents.
    """
    validation = validate_analysis_inputs(
        location=location,
        primary_cuisine=primary_cuisine,
        primary_rest_type=primary_rest_type,
        approx_costfor_two_people=approx_costfor_two_people,
        online_order=online_order,
        book_table=book_table,
    )
    if not validation["is_valid"]:
        return validation

    def notify(stage: str, status: str, message: str):
        if progress_callback:
            progress_callback(stage, status, message)

    notify("coordinator", "started", "Orchestrating specialist analysis")

    # 1. Location Analysis
    notify("location", "started", "Retrieving location context...")
    location_result = location_analysis_tool(location=location)
    notify("location", "completed", "Location context retrieved")

    # 2. Performance Prediction
    notify("performance", "started", "Running performance prediction...")
    perf_kwargs = {
        "online_order": online_order,
        "book_table": book_table,
        "approx_costfor_two_people": approx_costfor_two_people,
        "cost_band": cost_band,
        "location": location,
        "primary_cuisine": primary_cuisine,
        "cuisine_count": cuisine_count,
        "primary_rest_type": primary_rest_type,
    }
    if location_result and location_result.get("found", False):
        perf_kwargs.update({
            "historical_restaurant_count": location_result.get("historical_restaurant_count", 0),
            "location_median_cost": location_result.get("location_median_cost", 0.0),
            "location_online_order_rate": location_result.get("location_online_order_rate", 0.0),
            "location_book_table_rate": location_result.get("location_book_table_rate", 0.0),
            "location_cuisine_diversity": location_result.get("location_cuisine_diversity", 0),
            "location_business_type_diversity": location_result.get("location_business_type_diversity", 0),
        })
    if progress_callback:
        perf_kwargs["progress_callback"] = progress_callback
    performance_result = performance_analysis_tool(**perf_kwargs)

    # 3. Competition Analysis
    notify("competition", "started", "Retrieving nearby competitors...")
    effective_query = (
        search_query
        if isinstance(search_query, str) and search_query.strip()
        else f"{primary_cuisine or ''} restaurant in {location}".strip()
    )
    competition_result = competition_analysis_tool(
        location=location,
        search_query=effective_query,
        business_type="restaurant",
        radius_km=radius_km,
        max_results=max_results,
    )
    comp_count = competition_result.get("competitor_count", 0)
    notify("competition", "completed", f"{comp_count} competitors found")

    # 4. Opportunity Assessment
    notify("opportunity", "started", "Combining performance and competition signals...")
    opportunity_result = opportunity_analysis_tool(
        probabilities=performance_result["probabilities"],
        model_classes=list(performance_result["probabilities"].keys()),
        competition_summary=competition_result["competition_summary"],
    )
    score = opportunity_result.get("opportunity_score", {}).get("score", 0.0)
    signal = opportunity_result.get("opportunity_score", {}).get("signal", "Unknown")
    notify("opportunity", "completed", f"Opportunity score: {score:.1f} ({signal})")

    # 5. Financial Simulation
    notify("financial", "started", "Running 3-year cash flow simulation...")
    aov = (
        average_order_value
        if average_order_value is not None
        else (float(approx_costfor_two_people) / 2.0)
    )

    financial_result = simulate_financials(
        customers_per_day=float(customers_per_day),
        average_order_value=float(aov),
        rent=float(rent),
        staff_cost=float(staff_cost),
        food_cost_percent=float(food_cost_percent),
        utilities=float(utilities),
        marketing=float(marketing),
        other_expenses=float(other_expenses),
        working_days=float(working_days),
    )

    financial_result["customers_per_day"] = round(float(customers_per_day), 2)
    financial_result["average_order_value"] = round(float(aov), 2)
    financial_result["assumptions"] = {
        "customers_per_day": round(float(customers_per_day), 2),
        "average_order_value": round(float(aov), 2),
        "working_days": round(float(working_days), 2),
        "rent": round(float(rent), 2),
        "staff_cost": round(float(staff_cost), 2),
        "food_cost_percent": round(float(food_cost_percent), 2),
        "utilities": round(float(utilities), 2),
        "marketing": round(float(marketing), 2),
        "other_expenses": round(float(other_expenses), 2),
    }
    notify("financial", "completed", "Financial simulation completed")

    # 6. AI Insights Generation
    notify("insights", "started", "Generating AI insights across all sections...")

    analysis_payload = {
        "location_result": location_result,
        "performance_result": performance_result,
        "competition_result": competition_result,
        "opportunity_result": opportunity_result,
        "financial_result": financial_result,
        "financial": financial_result,
    }

    concept_context = {
        "location": location,
        "primary_cuisine": primary_cuisine,
        "primary_rest_type": primary_rest_type,
        "approx_cost_for_two": float(approx_costfor_two_people),
        "online_order": online_order,
        "book_table": book_table,
    }

    ai_insights = generate_business_insights(
        context=concept_context,
        analysis=analysis_payload,
    )
    analysis_payload["ai_insights"] = ai_insights

    notify("insights", "completed", "AI insights generated")
    notify("coordinator", "completed", "Full business analysis complete")

    return analysis_payload


COORDINATOR_SYSTEM_INSTRUCTION = """
You are the Master Coordinator Agent for BizAdvisor, an AI-powered business assessment system for restaurants in Bengaluru.

Your role:
- Orchestrate specialist analysis using run_full_business_analysis.
- Synthesize findings into a clear, structured advisory response.

Output requirements:
- Maximum 120 words total.
- Exactly 4 sections:
  1. Executive Summary (2 sentences max)
  2. Key Insights (2 bullet points)
  3. Key Risk (1 sentence)
  4. Next Step (1 concrete action)
- Be specific, actionable, and data-driven. Reference concrete numbers.
"""

coordinator_agent = Agent(
    name="coordinator_agent",
    model=PRIMARY_MODEL_NAME,
    description="Master coordinator that orchestrates restaurant business analysis.",
    instruction=COORDINATOR_SYSTEM_INSTRUCTION.strip(),
    tools=[
        AgentTool(agent=location_agent),
        AgentTool(agent=performance_agent),
        AgentTool(agent=competition_agent),
        AgentTool(agent=opportunity_agent),
        run_full_business_analysis,
    ],
)
