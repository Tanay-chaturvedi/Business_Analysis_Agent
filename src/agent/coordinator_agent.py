from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool    #AgentTool basically ek agent ko doosre agent ke liye callable tool bana deta hai.
from src.agent.llm_config import PRIMARY_MODEL_NAME

from src.agent.competition_agent import competition_agent
from src.agent.location_agent import location_agent
from src.agent.performance_agent import performance_agent
from src.agent.opportunity_agent import opportunity_agent

# Import the underlying tool functions directly so that the full-analysis
# orchestrator can call them in a guaranteed order from Python — not via
# LLM prompt instructions that only express a preference, not a hard constraint.
from src.agent.location_agent import location_analysis_tool
from src.agent.performance_agent import performance_analysis_tool
from src.agent.competition_agent import competition_analysis_tool
from src.agent.opportunity_agent import opportunity_analysis_tool
from src.finance.simulator import simulate_financials


def validate_analysis_inputs(
    location: str = None,
    primary_cuisine: str = None,
    primary_rest_type: str = None,
    approx_costfor_two_people: float = None,
    online_order: int = None,
    book_table: int = None,
) -> dict:
    """
    Validation layer verifying that all 6 required business-analysis inputs are available:
    1. location
    2. cuisine
    3. restaurant_type
    4. approx_costfor_two_people
    5. has_online_order
    6. has_table_booking
    """
    missing_inputs = []

    if location is None or str(location).strip().lower() in ("", "none", "missing", "unknown", "null"):
        missing_inputs.append("location")

    if primary_cuisine is None or str(primary_cuisine).strip().lower() in ("", "none", "missing", "unknown", "null"):
        missing_inputs.append("cuisine")

    if primary_rest_type is None or str(primary_rest_type).strip().lower() in ("", "none", "missing", "unknown", "null"):
        missing_inputs.append("restaurant_type")

    if approx_costfor_two_people is None or str(approx_costfor_two_people).strip().lower() in ("", "none", "missing", "unknown", "null"):
        missing_inputs.append("approx_costfor_two_people")

    if online_order is None or str(online_order).strip().lower() in ("", "none", "missing", "unknown", "null"):
        missing_inputs.append("has_online_order")

    if book_table is None or str(book_table).strip().lower() in ("", "none", "missing", "unknown", "null"):
        missing_inputs.append("has_table_booking")

    if missing_inputs:
        return {
            "status": "needs_input",
            "is_valid": False,
            "missing_inputs": missing_inputs
        }

    return {
        "status": "valid",
        "is_valid": True,
        "missing_inputs": []
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
    radius_km: float = 3.0,
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
    tool_context: ToolContext = None,
    progress_callback = None
) -> dict:
    """
    Orchestrate a full business analysis in guaranteed order:

        Step 1 – Location context (historical data for the target location)
        Step 2 – Performance prediction (ML model + SHAP)
        Step 3 – Competition analysis (Google Places)
        Step 4 – Opportunity analysis (requires ACTUAL Performance and
                  Competition outputs — runs only after they exist)

    Opportunity cannot execute before Performance and Competition because
    this function passes their actual return values as arguments.

    This tool preserves independent agent usage:
    - Use location_agent for location-only requests.
    - Use performance_agent for performance-only requests.
    - Use competition_agent for competition-only requests.
    - Use opportunity_agent when Performance and Competition data are
      already available.
    - Use this tool ONLY when a complete end-to-end analysis is required.
    """
    # ------------------------------------------------------------------ #
    # Step 0: Backend Required Input Validation                           #
    # ------------------------------------------------------------------ #
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
        progress_callback("coordinator", "started", "Orchestrating specialist analysis")

    # ------------------------------------------------------------------ #
    # Step 1: Location context                                             #
    # ------------------------------------------------------------------ #
    if progress_callback:
        progress_callback("location", "started", "Retrieving location context...")

    location_result = location_analysis_tool(
        location=location,
        tool_context=tool_context
    )

    if progress_callback:
        progress_callback("location", "completed", "Location context retrieved")

    # ------------------------------------------------------------------ #
    # Step 2: Performance prediction                                        #
    # Location context is read from tool_context.state by the tool if     #
    # historical_restaurant_count / location_median_cost are not passed.   #
    # ------------------------------------------------------------------ #
    perf_kwargs = dict(
        online_order=online_order,
        book_table=book_table,
        approx_costfor_two_people=approx_costfor_two_people,
        cost_band=cost_band,
        location=location,
        primary_cuisine=primary_cuisine,
        cuisine_count=cuisine_count,
        primary_rest_type=primary_rest_type,
        tool_context=tool_context,
    )
    if progress_callback:
        perf_kwargs["progress_callback"] = progress_callback

    performance_result = performance_analysis_tool(**perf_kwargs)

    # ------------------------------------------------------------------ #
    # Step 3: Competition analysis                                          #
    # business_type is always "restaurant" for food businesses.            #
    # ------------------------------------------------------------------ #
    if progress_callback:
        progress_callback("competition", "started", "Retrieving nearby competitors...")

    competition_result = competition_analysis_tool(
        location=location,
        search_query=search_query,
        business_type="restaurant",
        radius_km=radius_km,
        max_results=max_results,
        tool_context=tool_context
    )

    if progress_callback:
        comp_count = competition_result.get("competitor_count", 0)
        progress_callback("competition", "completed", f"{comp_count} competitors found")

    # ------------------------------------------------------------------ #
    # Step 4: Opportunity analysis                                          #
    # Opportunity receives the ACTUAL outputs of Steps 2 and 3.            #
    # It cannot reach this line before Steps 2 and 3 have returned.        #
    # ------------------------------------------------------------------ #
    if progress_callback:
        progress_callback("opportunity", "started", "Combining performance and competition signals...")

    prob_dict = performance_result["probabilities"]
    competition_summary = competition_result["competition_summary"]

    opportunity_result = opportunity_analysis_tool(
        probabilities=prob_dict,
        model_classes=list(prob_dict.keys()),
        competition_summary=competition_summary,
        tool_context=tool_context
    )

    if progress_callback:
        progress_callback("opportunity", "completed", "Opportunity assessment completed")

    # ------------------------------------------------------------------ #
    # Step 5: Financial analysis                                            #
    # ------------------------------------------------------------------ #
    if progress_callback:
        progress_callback("financial", "started", "Calculating revenue, expenses, and break-even...")

    aov = average_order_value if average_order_value is not None else (float(approx_costfor_two_people) / 2.0)

    financial_result = simulate_financials(
        customers_per_day=customers_per_day,
        average_order_value=aov,
        rent=rent,
        staff_cost=staff_cost,
        food_cost_percent=food_cost_percent,
        utilities=utilities,
        marketing=marketing,
        other_expenses=other_expenses,
        working_days=working_days,
    )
    financial_result["customers_per_day"] = round(customers_per_day, 2)
    financial_result["average_order_value"] = round(aov, 2)
    financial_result["assumptions"] = {
        "customers_per_day": round(customers_per_day, 2),
        "average_order_value": round(aov, 2),
        "working_days": round(working_days, 2),
        "rent": round(rent, 2),
        "staff_cost": round(staff_cost, 2),
        "food_cost_percent": round(food_cost_percent, 2),
        "utilities": round(utilities, 2),
        "marketing": round(marketing, 2),
        "other_expenses": round(other_expenses, 2),
    }

    if progress_callback:
        progress_callback("financial", "completed", "Financial analysis completed")

    if progress_callback:
        progress_callback("coordinator", "completed", "Orchestration completed")

    return {
        "location_result": location_result,
        "performance_result": performance_result,
        "competition_result": competition_result,
        "opportunity_result": opportunity_result,
        "financial_result": financial_result,
        "financial": financial_result,
    }


coordinator_agent = Agent(
    name="coordinator_agent",
    model=PRIMARY_MODEL_NAME,

    description=(
        "Coordinator agent responsible for understanding the user's "
        "business analysis request and delegating work to specialized agents."
    ),

    instruction="""
You are the Coordinator Agent for BizAdvisor, an AI business analysis system.

Your primary job is to understand the user's request, delegate work using specialized tools, and present a concise summary.

==================================================
TOOL DELEGATION RULES
==================================================

1. FULL BUSINESS ANALYSIS:
   When the user requests a complete business analysis, call:
       run_full_business_analysis
   Pass numeric parameters as numbers (e.g., approx_costfor_two_people=1200.0, online_order=1, book_table=1, radius_km=3.0).

2. FOCUSED REQUESTS:
   - For location-only: call location_agent
   - For performance-only: call performance_agent
   - For competition-only: call competition_agent with business_type="restaurant"
   - For opportunity-only: call opportunity_agent (requires Performance & Competition outputs)

==================================================
FINAL SYNTHESIS RESPONSE FORMAT
==================================================

CRITICAL LENGTH RULE: Your final synthesis response MUST BE EXTREMELY CONCISE (STRICT MAXIMUM OF 100 TO 120 WORDS TOTAL). DO NOT GENERATE LONG ESSAYS OR EXTENSIVE MULTI-PARAGRAPH RECOMMENDATION LISTS.

Format the response strictly using these 4 brief points:

1. **Executive Summary**: State the Opportunity Score & level (e.g., 62.66 - Moderate) and the ML Model Prediction (e.g., High performance).
2. **Key Insights**: State 2-3 short bullet insights derived directly from the returned tool data (e.g., strong location demand, 62% operating profit margin).
3. **Key Risk**: State 1 primary risk (e.g., high competition strength).
4. **Next Step**: State 1 clear, actionable next step for the business owner.

RULES:
- Do NOT repeat raw tables, detailed competitor lists, or numbers already displayed in UI cards.
- Use ONLY the actual returned tool outputs. Do not invent or recalculate numbers.
- Do NOT claim SHAP or historical features are causal guarantees.
- Do NOT exceed 120 words under any circumstances.
""",

    tools=[
        AgentTool(agent=location_agent),
        AgentTool(agent=performance_agent),
        AgentTool(agent=competition_agent),
        AgentTool(agent=opportunity_agent),
        run_full_business_analysis,
    ],
)