"""
adk_runner.py — Genuine Google ADK Runtime Integration

This module executes the coordinator_agent through the genuine
google.adk Runner + InMemorySessionService runtime loop.

When Gemini is reachable:
    - Runner.run_async() is used to drive the coordinator_agent.
    - The coordinator_agent calls run_full_business_analysis as a tool.
    - Tool call results are extracted from ADK Event objects.
    - The structured analysis dict is returned to server.py.

When Gemini returns a 403/404 (API unavailable):
    - Falls back to run_full_business_analysis() direct Python call.
    - The same structured result dict is returned.
    - The fallback is logged clearly so it is never hidden.

IMPORTANT: All domain calculations (ML, SHAP, Google Places, opportunity)
remain in the existing src/ modules. The ADK runner only orchestrates the
agent loop — it does NOT replace or alter any calculation logic.
"""

import asyncio
import json
import uuid
import logging
from typing import Any, Dict, Optional

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from src.agent.coordinator_agent import (
    coordinator_agent,
    run_full_business_analysis,
    validate_analysis_inputs,
)

logger = logging.getLogger(__name__)


# ADK Application name (required by InMemorySessionService)
_ADK_APP_NAME = "bizadvisor"



# Helper: extract the run_full_business_analysis result from ADK events

def _extract_tool_result_from_events(events: list) -> Optional[Dict[str, Any]]:
    """
    Scan the list of ADK Event objects produced by Runner.run_async() and
    extract the structured result dict returned by run_full_business_analysis.

    The tool result is stored in the FunctionResponse part of an event whose
    author is 'tool' or whose content parts contain FunctionResponse objects.

    Returns the parsed result dict, or None if it cannot be found.
    """
    tool_name = "run_full_business_analysis"

    for event in events:
        # event.content may be None for non-content events
        if event.content is None:
            continue

        parts = event.content.parts or []
        for part in parts:
            # FunctionResponse carries the tool's return value
            if hasattr(part, "function_response") and part.function_response is not None:
                fr = part.function_response
                # Match specifically the tool we care about
                if fr.name == tool_name:
                    response_data = fr.response
                    if isinstance(response_data, dict):
                        return response_data
                    # Sometimes ADK wraps the dict in a 'result' key
                    if isinstance(response_data, dict) and "result" in response_data:
                        result = response_data["result"]
                        if isinstance(result, dict):
                            return result
    return None


# Core async function: run coordinator_agent via ADK runtime
async def _run_via_adk_async(
    location: str,
    search_query: str,
    online_order: int,
    book_table: int,
    approx_cost: float,
    cost_band: str,
    primary_cuisine: str,
    cuisine_count: int,
    rest_type: str,
    radius_km: float,
    session_id: str,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Internal async implementation that runs one coordinator_agent turn
    through the genuine ADK Runner + InMemorySessionService.

    Raises any exception so the caller (_run_analysis) can catch it and
    fall back to the direct Python pipeline.
    """
    session_service = InMemorySessionService()

    # create_session is async in ADK 2.6.x — must be awaited
    session = await session_service.create_session(
        app_name=_ADK_APP_NAME,
        user_id="bizadvisor_user",
        session_id=session_id,
    )

    runner = Runner(
        agent=coordinator_agent,
        app_name=_ADK_APP_NAME,
        session_service=session_service,
    )

    # Build the user message that instructs the coordinator to run a full analysis
    user_prompt = (
        f"Run a complete business analysis for the following restaurant concept:\n"
        f"  Location: {location}\n"
        f"  Cuisine: {primary_cuisine}\n"
        f"  Cost for two: ₹{int(approx_cost)}\n"
        f"  Cost band: {cost_band}\n"
        f"  Restaurant type: {rest_type}\n"
        f"  Online ordering: {'Yes' if online_order else 'No'}\n"
        f"  Table booking: {'Yes' if book_table else 'No'}\n"
        f"  Cuisine count: {cuisine_count}\n"
        f"  Competitor search query: {search_query}\n"
        f"  Search radius: {radius_km} km\n\n"
        f"Use run_full_business_analysis to perform the complete analysis pipeline "
        f"(Location → Performance → Competition → Opportunity) and return all results."
    )

    new_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_prompt)],
    )

    if progress_callback:
        progress_callback("adk_runner", "started", "ADK runtime executing coordinator_agent...")

    collected_events = []
    async for event in runner.run_async(
        user_id="bizadvisor_user",
        session_id=session_id,
        new_message=new_message,
    ):
        collected_events.append(event)
        logger.debug("[ADK Runner] Event author=%s is_final=%s", event.author, event.is_final_response())

    if progress_callback:
        progress_callback("adk_runner", "completed", f"ADK runner collected {len(collected_events)} events")

    # Extract the structured tool result from the collected events
    result = _extract_tool_result_from_events(collected_events)

    if result is not None:
        logger.info("[ADK Runner] Successfully extracted run_full_business_analysis result from ADK events.")
        return result

    # The agent ran but we could not extract the tool result.
    # This can happen if the LLM chose not to call the tool.
    # Fall back to direct Python call with the same parameters.
    logger.warning(
        "[ADK Runner] Could not extract tool result from ADK events. "
        "Falling back to direct Python pipeline."
    )
    return run_full_business_analysis(
        location=location,
        search_query=search_query,
        online_order=online_order,
        book_table=book_table,
        approx_costfor_two_people=approx_cost,
        cost_band=cost_band,
        primary_cuisine=primary_cuisine,
        cuisine_count=cuisine_count,
        primary_rest_type=rest_type,
        radius_km=radius_km,
        progress_callback=progress_callback,
    )



# Public synchronous entry point used by server.py

def run_analysis_via_adk(
    location: str = None,
    search_query: str = None,
    online_order: int = None,
    book_table: int = None,
    approx_cost: float = None,
    cost_band: str = "Medium",
    primary_cuisine: str = None,
    cuisine_count: int = 2,
    rest_type: str = None,
    radius_km: float = 3.0,
    session_id: Optional[str] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Public synchronous entry point that runs a full business analysis.
    Validates required inputs first. If any required input is missing, returns needs_input status.
    """
    validation = validate_analysis_inputs(
        location=location,
        primary_cuisine=primary_cuisine,
        primary_rest_type=rest_type,
        approx_costfor_two_people=approx_cost,
        online_order=online_order,
        book_table=book_table,
    )
    if not validation["is_valid"]:
        return validation

    _session_id = session_id or str(uuid.uuid4())

    # ── Attempt 1: genuine ADK runtime ────────────────────────────────────────
    try:
        result = asyncio.run(
            _run_via_adk_async(
                location=location,
                search_query=search_query,
                online_order=online_order,
                book_table=book_table,
                approx_cost=approx_cost,
                cost_band=cost_band,
                primary_cuisine=primary_cuisine,
                cuisine_count=cuisine_count,
                rest_type=rest_type,
                radius_km=radius_km,
                session_id=_session_id,
                progress_callback=progress_callback,
            )
        )
        result["_orchestration"] = "adk_runtime"
        return result

    except Exception as adk_error:
        error_str = str(adk_error)

        # Log clearly — never silently hide the ADK failure
        if "403" in error_str or "PERMISSION_DENIED" in error_str or "Unauthorized" in error_str:
            logger.warning(
                "[ADK Fallback] LLM returned 403 / Authentication Error. "
                "Running direct Python pipeline. Fix: update API key in .env."
            )
            print(
                "[ADK Fallback] LLM 403 / Authentication Error — "
                "running deterministic Python pipeline as fallback."
            )
        elif "404" in error_str or "NOT_FOUND" in error_str or "model_not_found" in error_str:
            logger.warning(
                "[ADK Fallback] LLM returned 404 / Model Not Found (model unavailable). "
                "Running direct Python pipeline."
            )
            print(
                "[ADK Fallback] LLM 404 / Model Not Found — "
                "running deterministic Python pipeline as fallback."
            )
        else:
            logger.exception("[ADK Fallback] Unexpected ADK error: %s", adk_error)
            print(f"[ADK Fallback] ADK error: {adk_error!r} — running deterministic Python pipeline.")

    # ── Fallback: direct Python pipeline ──────────────────────────────────────
    result = run_full_business_analysis(
        location=location,
        search_query=search_query,
        online_order=online_order,
        book_table=book_table,
        approx_costfor_two_people=approx_cost,
        cost_band=cost_band,
        primary_cuisine=primary_cuisine,
        cuisine_count=cuisine_count,
        primary_rest_type=rest_type,
        radius_km=radius_km,
        progress_callback=progress_callback,
    )
    result["_orchestration"] = "python_fallback"
    return result
