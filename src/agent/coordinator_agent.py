from google.adk.agents import Agent
from google.adk.tools import ToolContext
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
from src.finance.simulator import simulate_financials


def validate_analysis_inputs(
    location=None,
    primary_cuisine=None,
    primary_rest_type=None,
    approx_costfor_two_people=None,
    online_order=None,
    book_table=None,
) -> dict:

    inputs = {
        "location": location,
        "cuisine": primary_cuisine,
        "restaurant_type": primary_rest_type,
        "approx_costfor_two_people": approx_costfor_two_people,
        "has_online_order": online_order,
        "has_table_booking": book_table,
    }

    missing = [
        key
        for key, value in inputs.items()
        if value is None
        or str(value).strip().lower() in ("", "none", "missing", "unknown", "null")
    ]

    if missing:
        return {
            "status": "needs_input",
            "is_valid": False,
            "missing_inputs": missing,
        }

    return {
        "status": "valid",
        "is_valid": True,
        "missing_inputs": [],
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
    initial_investment: float = 2000000.0,
    monthly_fixed_costs: float = 150000.0,
    rent: float = 60000.0,
    average_order_value: float = None,
    gross_margin_pct: float = 0.65,
    cost_of_goods_sold_pct: float = 0.35,
    marketing_budget: float = 30000.0,
    target_payback_months: int = 18,
    scenario_growth_rate: float = 0.05,
    tax_rate: float = 0.05,
    tool_context: ToolContext = None,
    progress_callback=None,
) -> dict:

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

    if progress_callback:
        progress_callback(
            "coordinator", "started", "Orchestrating specialist analysis"
        )

    # 1. Location Analysis
    if progress_callback:
        progress_callback("location", "started", "Retrieving location context...")
    location_result = location_analysis_tool(
        location=location, tool_context=tool_context
    )
    if progress_callback:
        progress_callback(
            "location", "completed", "Location context retrieved"
        )

    # 2. Performance Prediction
    if progress_callback:
        progress_callback(
            "performance", "started", "Running performance prediction..."
        )
    perf_kwargs = {
        "online_order": online_order,
        "book_table": book_table,
        "approx_costfor_two_people": approx_costfor_two_people,
        "cost_band": cost_band,
        "location": location,
        "primary_cuisine": primary_cuisine,
        "cuisine_count": cuisine_count,
        "primary_rest_type": primary_rest_type,
        "tool_context": tool_context,
    }
    if progress_callback:
        perf_kwargs["progress_callback"] = progress_callback
    performance_result = performance_analysis_tool(**perf_kwargs)

    # 3. Competition Analysis
    if progress_callback:
        progress_callback(
            "competition", "started", "Retrieving nearby competitors..."
        )
    competition_result = competition_analysis_tool(
        location=location,
        search_query=search_query,
        business_type="restaurant",
        radius_km=radius_km,
        max_results=max_results,
        tool_context=tool_context,
    )
    if progress_callback:
        comp_count = competition_result.get("competitor_count", 0)
        progress_callback(
            "competition", "completed", f"{comp_count} competitors found"
        )

    # 4. Opportunity Assessment
    if progress_callback:
        progress_callback(
            "opportunity",
            "started",
            "Combining performance and competition signals...",
        )
    opportunity_result = opportunity_analysis_tool(
        probabilities=performance_result["probabilities"],
        model_classes=performance_result["model_classes"],
        competition_summary=competition_result["competition_summary"],
        tool_context=tool_context,
    )
    if progress_callback:
        score = opportunity_result.get("opportunity_score", {}).get("score", 0.0)
        signal = opportunity_result.get("opportunity_score", {}).get(
            "signal", "Unknown"
        )
        progress_callback(
            "opportunity", "completed", f"Opportunity score: {score:.1f} ({signal})"
        )

    # 5. Financial Simulation
    if progress_callback:
        progress_callback(
            "financial", "started", "Running 3-year cash flow simulation..."
        )

    aov = (
        average_order_value
        if average_order_value is not None
        else (float(approx_costfor_two_people) / 2.0)
    )

    assumptions = {
        "initial_investment": round(float(initial_investment), 2),
        "monthly_fixed_costs": round(float(monthly_fixed_costs), 2),
        "rent": round(float(rent), 2),
        "average_order_value": round(float(aov), 2),
        "gross_margin_pct": round(float(gross_margin_pct), 2),
        "cost_of_goods_sold_pct": round(float(cost_of_goods_sold_pct), 2),
        "marketing_budget": round(float(marketing_budget), 2),
        "target_payback_months": int(target_payback_months),
        "scenario_growth_rate": round(float(scenario_growth_rate), 2),
        "tax_rate": round(float(tax_rate), 2),
    }

    financial_result = simulate_financials(
        performance_result=performance_result,
        opportunity_result=opportunity_result,
        assumptions=assumptions,
    )

    financial_result["average_order_value"] = assumptions["average_order_value"]
    financial_result["assumptions"] = assumptions

    if progress_callback:
        progress_callback(
            "financial", "completed", "Financial simulation completed"
        )
        progress_callback(
            "coordinator", "completed", "Full business analysis complete"
        )

    return {
        "location_result": location_result,
        "performance_result": performance_result,
        "competition_result": competition_result,
        "opportunity_result": opportunity_result,
        "financial_result": financial_result,
        "financial": financial_result,
    }


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
