"""
BizAdvisor FastAPI Server
==========================
API layer connecting the BizAdvisor Chat Frontend to the existing AI/ML agents,
Google ADK, Gemini, Random Forest model, and Google Places integration.

Do NOT recalculate ML probabilities or opportunity score in this file;
delegate all domain calculations to existing backend modules in src/.
"""

import os
import json
import uuid
import datetime

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Import existing backend modules
from src.agent.coordinator_agent import run_full_business_analysis, coordinator_agent
from src.agent.adk_runner import run_analysis_via_adk  # Genuine ADK runtime wrapper
from src.analysis.what_if import compare_ml_scenarios, compare_financial_scenarios
from src.analysis.location_context import get_location_context
from src.ml.predictor import predict_business_performance
from src.places.competition import summarize_competition, search_competitors_by_text

# Import authentication and security
from src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    validate_username,
    validate_email,
    validate_password_strength,
)
from src.database import (
    init_db as init_mysql_db,
    SessionLocal,
    User,
    Conversation,
    Message,
    get_or_create_conversation,
    save_chat_turn,
    get_conversation_list,
    get_conversation_detail,
    delete_conversation,
    get_db,
)

load_dotenv()

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

app = FastAPI(
    title="BizAdvisor API",
    description="AI Business Intelligence & Decision Support Platform API",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Secure CORS Configuration
allowed_origins_env = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
)
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Global Safe Exception Handler (prevents leaking internal traces, passwords, or SQL queries)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logger = logging.getLogger("bizadvisor.api")
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None)
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )

init_mysql_db()


# -----------------------------------------------------------------------------
# BUSINESS TAKEAWAY BUILDER
# -----------------------------------------------------------------------------

def build_business_takeaway(
    location: str,
    cuisine: str,
    rest_type: str,
    analysis: dict,
) -> str:
    """
    Generate a rich, conversational 3-4 sentence Business Takeaway from real
    analysis results.  This is the SINGLE SOURCE OF TRUTH for the takeaway text
    displayed in the UI and read aloud by the TTS feature.

    Rules:
    - Every value is sourced from the backend analysis dict.
    - Do NOT invent, assume, or hard-code any numbers.
    - Language is balanced: acknowledges positives AND constraints.
    - Avoids guaranteeing revenue, profit, or business success.
    - Targets 50-80 words for comfortable TTS reading.
    """
    opp  = analysis.get("opportunity_result", {})
    perf = analysis.get("performance_result", {})
    comp_res = analysis.get("competition_result", {})

    # --- Opportunity ---
    opp_score  = opp.get("opportunity_score", {}).get("score", None)
    opp_signal = opp.get("opportunity_score", {}).get("signal", "Moderate")  # Low | Moderate | High

    # --- Performance ---
    pred_class = perf.get("prediction", "Moderate")          # High | Medium | Low
    high_prob  = perf.get("probabilities", {}).get("High")
    high_prob_pct = f"{round(high_prob * 100)}%" if high_prob is not None else None

    hist_perf  = opp.get("historical_performance", {})
    perf_signal = hist_perf.get("signal", "")  # e.g. "Strong historical performance"

    # --- Competition ---
    comp_strength  = opp.get("competition_strength", {})
    comp_signal_raw = comp_strength.get("signal", "Moderate competition")  # e.g. "Strong competition"

    comp_summary   = comp_res.get("competition_summary") or {}
    comp_count     = comp_summary.get("competitor_count_retrieved") or comp_res.get("competitor_count", 0)
    high_rated     = comp_summary.get("high_rating_competitors", 0)

    # --- Location ---
    loc_short = location.split(",")[0].strip()  # e.g. "Koramangala"

    # ── Sentence 1: Concept + performance signal ─────────────────────────────
    prob_clause = f", with the model indicating a {high_prob_pct} probability of high performance" if high_prob_pct else ""
    s1 = (
        f"The {cuisine} {rest_type.lower()} concept in {loc_short} shows "
        f"{perf_signal.lower() if perf_signal else 'a moderate historical performance signal'}"
        f"{prob_clause}."
    )

    # ── Sentence 2: Competition context ──────────────────────────────────────
    if comp_count and int(comp_count) > 0:
        if "strong" in comp_signal_raw.lower():
            comp_desc = (
                f"The area has {int(comp_count)} nearby competitors with {high_rated} rated at 4.5 stars or above, "
                f"indicating a competitive market where differentiation in cuisine, pricing, or experience will be important."
            )
        elif "limited" in comp_signal_raw.lower():
            comp_desc = (
                f"With only {int(comp_count)} nearby competitors and limited saturation, "
                f"this location presents a relatively open window for a new entrant."
            )
        else:
            comp_desc = (
                f"The area has {int(comp_count)} nearby competitors, reflecting moderate market activity — "
                f"solid differentiation could give this concept a meaningful edge."
            )
    else:
        comp_desc = "Competition data was not available for this location, so market saturation is unclear."

    # ── Sentence 3: Overall opportunity verdict ───────────────────────────────
    if opp_signal == "High":
        verdict = (
            f"Overall, the data points toward a {opp_score}-out-of-100 opportunity score, "
            f"suggesting a favourable environment for this concept."
        )
    elif opp_signal == "Low":
        verdict = (
            f"Overall, the opportunity score of {opp_score} out of 100 signals a challenging environment, "
            f"and significant strategic planning would be needed before moving forward."
        )
    else:
        verdict = (
            f"Overall, the analysis gives this concept an opportunity score of {opp_score} out of 100, "
            f"indicating a reasonable but not guaranteed path forward."
        )

    # ── Sentence 4: Disclaimer ────────────────────────────────────────────────
    disclaimer = (
        "This should be treated as a data-backed indication rather than a guarantee of business success — "
        "real-world execution, local relationships, and market timing also play a critical role."
    )

    return f"{s1} {comp_desc} {verdict} {disclaimer}"


# -----------------------------------------------------------------------------
# PYDANTIC SCHEMAS
# -----------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: str = Field(...)
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    username_or_email: str = Field(...)
    password: str = Field(...)

class AnalyzeRequest(BaseModel):
    location: str = Field(..., example="Koramangala, Bengaluru")
    primary_cuisine: str = Field(default="North Indian", example="Japanese")
    approx_cost_for_two: float = Field(default=800.0, example=1800.0)
    online_order: bool = Field(default=True)
    book_table: bool = Field(default=True)
    cuisine_count: int = Field(default=2)
    restaurant_type: str = Field(default="Casual Dining")
    search_query: Optional[str] = None
    radius_km: float = Field(default=3.0)

class ChatRequest(BaseModel):
    message: str = Field(..., example="I want to open a premium Japanese restaurant in Koramangala, Bengaluru. Cost for two is ₹1800.")
    session_id: Optional[str] = None
    parameters_override: Optional[Dict[str, Any]] = None

class ScenarioRequest(BaseModel):
    baseline_params: Dict[str, Any]
    scenario_params: Dict[str, Any]
    session_id: Optional[str] = None


class FinancialSimulateRequest(BaseModel):
    customers_per_day: float = Field(default=100.0, ge=0)
    average_order_value: float = Field(default=400.0, ge=0)
    rent: float = Field(default=60000.0, ge=0)
    staff_cost: float = Field(default=50000.0, ge=0)
    food_cost_percent: float = Field(default=30.0, ge=0, le=100)
    utilities: float = Field(default=15000.0, ge=0)
    marketing: float = Field(default=10000.0, ge=0)
    other_expenses: float = Field(default=5000.0, ge=0)
    working_days: float = Field(default=30.0, ge=1, le=31)


# -----------------------------------------------------------------------------
def normalize_location(loc_val: Optional[str]) -> Optional[str]:
    if not loc_val or not isinstance(loc_val, str):
        return None
    loc_clean = loc_val.strip()
    loc_lower = loc_clean.lower()
    location_map = [
        ("hsr layout", "HSR Layout, Bengaluru"),
        ("hsr", "HSR Layout, Bengaluru"),
        ("indiranagar", "Indiranagar, Bengaluru"),
        ("whitefield", "Whitefield, Bengaluru"),
        ("jayanagar", "Jayanagar, Bengaluru"),
        ("mg road", "MG Road, Bengaluru"),
        ("brookefield", "Brookefield, Bengaluru"),
        ("bellandur", "Bellandur, Bengaluru"),
        ("jp nagar", "JP Nagar, Bengaluru"),
        ("marathahalli", "Marathahalli, Bengaluru"),
        ("electronic city", "Electronic City, Bengaluru"),
        ("sarjapur", "Sarjapur Road, Bengaluru"),
        ("btm layout", "BTM Layout, Bengaluru"),
        ("btm", "BTM Layout, Bengaluru"),
        ("malleshwaram", "Malleshwaram, Bengaluru"),
        ("rajajinagar", "Rajajinagar, Bengaluru"),
        ("yelahanka", "Yelahanka, Bengaluru"),
        ("hebbal", "Hebbal, Bengaluru"),
        ("ulsoor", "Ulsoor, Bengaluru"),
        ("banaswadi", "Banaswadi, Bengaluru"),
        ("bannerghatta", "Bannerghatta Road, Bengaluru"),
        ("kengeri", "Kengeri, Bengaluru"),
        ("banashankari", "Banashankari, Bengaluru"),
        ("devanahalli", "Devanahalli, Bengaluru"),
        ("koramangala", "Koramangala, Bengaluru"),
    ]
    for keyword, canonical in location_map:
        if keyword in loc_lower:
            return canonical
    if "bengaluru" not in loc_lower and "bangalore" not in loc_lower:
        return f"{loc_clean.title()}, Bengaluru"
    return loc_clean.title()


def extract_business_parameters(user_message: str) -> dict:
    """
    Extract structured business analysis parameters from user natural language prompt.
    IMPORTANT: NEVER guess, assume, invent, or infer missing parameters.
    If a parameter is not explicitly provided in user_message, set its value to None.
    """
    msg_lower = user_message.lower().strip()
    import re

    # 1. Location
    location = None
    location_map = [
        ("hsr layout", "HSR Layout, Bengaluru"),
        ("hsr", "HSR Layout, Bengaluru"),
        ("indiranagar", "Indiranagar, Bengaluru"),
        ("whitefield", "Whitefield, Bengaluru"),
        ("jayanagar", "Jayanagar, Bengaluru"),
        ("mg road", "MG Road, Bengaluru"),
        ("brookefield", "Brookefield, Bengaluru"),
        ("bellandur", "Bellandur, Bengaluru"),
        ("jp nagar", "JP Nagar, Bengaluru"),
        ("marathahalli", "Marathahalli, Bengaluru"),
        ("electronic city", "Electronic City, Bengaluru"),
        ("sarjapur", "Sarjapur Road, Bengaluru"),
        ("btm layout", "BTM Layout, Bengaluru"),
        ("btm", "BTM Layout, Bengaluru"),
        ("malleshwaram", "Malleshwaram, Bengaluru"),
        ("rajajinagar", "Rajajinagar, Bengaluru"),
        ("yelahanka", "Yelahanka, Bengaluru"),
        ("hebbal", "Hebbal, Bengaluru"),
        ("ulsoor", "Ulsoor, Bengaluru"),
        ("banaswadi", "Banaswadi, Bengaluru"),
        ("bannerghatta", "Bannerghatta Road, Bengaluru"),
        ("kengeri", "Kengeri, Bengaluru"),
        ("banashankari", "Banashankari, Bengaluru"),
        ("devanahalli", "Devanahalli, Bengaluru"),
        ("koramangala", "Koramangala, Bengaluru"),
    ]
    for keyword, loc_name in location_map:
        if keyword in msg_lower:
            location = loc_name
            break

    if not location:
        # Regex check for "in <Location>"
        loc_match = re.search(r'\bin\s+([a-zA-Z\s]{3,20})(?:\,|\.|\s+bengaluru|\s+bangalore|$)', user_message, re.IGNORECASE)
        if loc_match:
            candidate = loc_match.group(1).strip().title()
            skip_words = ["a", "the", "north", "south", "cheap", "expensive", "casual", "fine"]
            if candidate.lower() not in skip_words and len(candidate) > 2:
                location = f"{candidate}, Bengaluru"

    # 2. Cuisine
    cuisine = None
    cuis_map = [
        ("north indian", "North Indian"),
        ("south indian", "South Indian"),
        ("japanese", "Japanese"),
        ("sushi", "Japanese"),
        ("korean", "Korean"),
        ("italian", "Italian"),
        ("pizza", "Italian"),
        ("chinese", "Chinese"),
        ("biryani", "Biryani"),
        ("ice cream", "Ice Cream"),
        ("icecream", "Ice Cream"),
        ("gelato", "Ice Cream"),
        ("dessert", "Dessert"),
        ("waffle", "Dessert"),
        ("brownie", "Dessert"),
        ("bakery", "Bakery"),
        ("burger", "Burger"),
        ("cafe", "Cafe"),
        ("café", "Cafe"),
        ("coffee", "Cafe"),
        ("continental", "Continental"),
        ("mexican", "Mexican"),
        ("thai", "Thai"),
        ("kebab", "North Indian"),
        ("mughlai", "North Indian"),
        ("seafood", "Seafood"),
    ]
    for keyword, cname in cuis_map:
        if keyword in msg_lower:
            cuisine = cname
            break

    # 3. Restaurant Type & Ambiguity Check
    rest_type = None
    rest_type_ambiguous = False
    if "fine dining" in msg_lower or "fine diner" in msg_lower:
        rest_type = "Fine Dining"
    elif "casual dining" in msg_lower or "casual diner" in msg_lower:
        rest_type = "Casual Dining"
    elif "cafe" in msg_lower or "café" in msg_lower or "coffee shop" in msg_lower:
        rest_type = "Cafe"
    elif "qsr" in msg_lower or "quick service" in msg_lower or "quick bytes" in msg_lower or "fast food" in msg_lower:
        rest_type = "Quick Bytes"
    elif "bakery" in msg_lower:
        rest_type = "Bakery"
    elif "dessert parlor" in msg_lower or "dessert parlour" in msg_lower or "ice cream parlor" in msg_lower:
        rest_type = "Dessert Parlor"
    elif any(k in msg_lower for k in ["premium restaurant", "nice restaurant", "small restaurant"]):
        if not any(t in msg_lower for t in ["fine dining", "casual dining", "cafe", "qsr", "bakery"]):
            rest_type_ambiguous = True

    # 4. Cost for Two & Ambiguity Check
    cost = None
    cost_ambiguous = False

    # Ambiguous terms check: e.g. "cheap", "budget", "expensive" without specific number
    if any(term in msg_lower for term in ["cheap", "budget", "affordable", "expensive", "high end", "high-end"]) and not re.search(r'\d{3,5}|\d+(?:\.\d+)?\s*k\b', msg_lower):
        cost_ambiguous = True
    else:
        # Match k expressions: "1.2k", "1.5k", "2k"
        m_k = re.search(r'(?:₹|rs\.?\s*|inr\s*|cost\s*(?:for\s+two\s*)?|price\s*)?(\d+(?:\.\d+)?)\s*k\b', msg_lower)
        if m_k:
            try:
                cost = float(m_k.group(1)) * 1000.0
            except ValueError:
                pass

        if cost is None:
            # Match standard numbers: "₹1,200", "₹1200", "1200 rupees", "1200 inr", "rs 1200", "cost 1200", "1200 for two"
            m_cost = re.search(r'(?:₹|rs\.?\s*|inr\s*|cost\s+(?:for\s+two\s+|of\s+|for\s+)?|price\s+(?:is\s+|to\s+|at\s+)?|to\s+₹?|at\s+₹?)(\d{1,2}[,\.]?\d{3}|\d{3,5})', msg_lower)
            if not m_cost:
                m_cost = re.search(r'(?:price|cost|budget|for\s+two|₹)\D{0,10}(\d{1,2}[,\.]?\d{3}|\d{3,5})', msg_lower)
            if m_cost:
                try:
                    c_val = float(m_cost.group(1).replace(',', ''))
                    if 50 <= c_val <= 20000:
                        cost = c_val
                except ValueError:
                    pass

    # 5. Online Ordering
    online_order = None
    if any(p in msg_lower for p in ["online order yes", "online ordering yes", "online yes", "delivery yes", "swiggy yes", "zomato yes", "online: yes", "online order = yes", "online_order: yes", "online = yes", "online ordering: yes", "online ordering = yes"]):
        online_order = True
    elif any(p in msg_lower for p in ["online order no", "online ordering no", "online no", "no online order", "no online ordering", "no delivery", "online: no", "online order = no", "online_order: no", "online = no", "online ordering: no", "online ordering = no"]):
        online_order = False

    # 6. Table Booking
    book_table = None
    if any(p in msg_lower for p in ["table booking yes", "book table yes", "table yes", "reservation yes", "table booking = yes", "table booking: yes", "table: yes", "book_table: yes", "table = yes", "table booking true"]):
        book_table = True
    elif any(p in msg_lower for p in ["table booking no", "book table no", "table no", "no table booking", "no book table", "no reservation", "table booking = no", "table booking: no", "table: no", "book_table: no", "table = no", "table booking false"]):
        book_table = False

    return {
        "location": location,
        "primary_cuisine": cuisine,
        "restaurant_type": rest_type,
        "approx_cost_for_two": cost,
        "online_order": online_order,
        "book_table": book_table,
        "cost_ambiguous": cost_ambiguous,
        "rest_type_ambiguous": rest_type_ambiguous,
    }


def parse_user_query(user_message: str) -> Dict[str, Any]:
    """
    Extract business analysis parameters from user message.
    NEVER guess or supply default values for missing inputs.
    """
    api_key = os.getenv("PRIMARY_LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    extracted = None

    if api_key:
        try:
            from src.agent.llm_config import PRIMARY_MODEL_NAME
            import litellm
            prompt = f"""
            You are a strict business analysis parameter extractor.
            Extract business parameters from the following user query for a restaurant business analysis.

            User Query: "{user_message}"

            Return ONLY a JSON object with these exact keys:
            - "location": str or null (e.g. "Koramangala, Bengaluru" or extracted location, null if unspecified)
            - "primary_cuisine": str or null (e.g. "Japanese", "North Indian", null if unspecified)
            - "approx_cost_for_two": float or null (number in INR, e.g. 1200.0. Convert "1.2k" to 1200.0. null if unspecified)
            - "cost_ambiguous": bool (true ONLY if user mentions "cheap", "expensive", "budget" without a specific number)
            - "restaurant_type": str or null ("Casual Dining", "Fine Dining", "Quick Bytes", "Cafe", "Bakery", "Dessert Parlor", null if unspecified)
            - "rest_type_ambiguous": bool (true ONLY if user mentions "premium restaurant" without specific category)
            - "online_order": bool or null (true if user specifies yes/yeah/online ordering, false if no/nah, null if unspecified)
            - "book_table": bool or null (true if user specifies yes/yeah/table booking, false if no/nah, null if unspecified)

            RULES:
            - DO NOT guess, assume, invent, or infer missing values. If not explicitly provided, return null.
            - Do not include markdown formatting or backticks around the JSON.
            """
            response = litellm.completion(
                model=PRIMARY_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.choices[0].message.content.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            extracted = json.loads(raw_text)
        except Exception as e:
            print(f"[QueryParser Warning] LLM extraction error: {e}. Using rule-based extractor.")

    if not extracted:
        extracted = extract_business_parameters(user_message)
    else:
        rule_extracted = extract_business_parameters(user_message)
        for k, v in rule_extracted.items():
            if extracted.get(k) is None and v is not None:
                extracted[k] = v

    # Canonical location normalization
    loc_val = extracted.get("location")
    if loc_val and isinstance(loc_val, str):
        loc_clean = loc_val.strip()
        loc_lower = loc_clean.lower()
        location_map = [
            ("hsr layout", "HSR Layout, Bengaluru"),
            ("hsr", "HSR Layout, Bengaluru"),
            ("indiranagar", "Indiranagar, Bengaluru"),
            ("whitefield", "Whitefield, Bengaluru"),
            ("jayanagar", "Jayanagar, Bengaluru"),
            ("mg road", "MG Road, Bengaluru"),
            ("brookefield", "Brookefield, Bengaluru"),
            ("bellandur", "Bellandur, Bengaluru"),
            ("jp nagar", "JP Nagar, Bengaluru"),
            ("marathahalli", "Marathahalli, Bengaluru"),
            ("electronic city", "Electronic City, Bengaluru"),
            ("sarjapur", "Sarjapur Road, Bengaluru"),
            ("btm layout", "BTM Layout, Bengaluru"),
            ("btm", "BTM Layout, Bengaluru"),
            ("malleshwaram", "Malleshwaram, Bengaluru"),
            ("rajajinagar", "Rajajinagar, Bengaluru"),
            ("yelahanka", "Yelahanka, Bengaluru"),
            ("hebbal", "Hebbal, Bengaluru"),
            ("ulsoor", "Ulsoor, Bengaluru"),
            ("banaswadi", "Banaswadi, Bengaluru"),
            ("bannerghatta", "Bannerghatta Road, Bengaluru"),
            ("kengeri", "Kengeri, Bengaluru"),
            ("banashankari", "Banashankari, Bengaluru"),
            ("devanahalli", "Devanahalli, Bengaluru"),
            ("koramangala", "Koramangala, Bengaluru"),
        ]
        matched_loc = None
        for keyword, canonical in location_map:
            if keyword in loc_lower:
                matched_loc = canonical
                break
        if matched_loc:
            extracted["location"] = matched_loc
        elif "bengaluru" not in loc_lower and "bangalore" not in loc_lower:
            extracted["location"] = f"{loc_clean.title()}, Bengaluru"

    # Clear ambiguous flags if explicit parameter values are provided
    if extracted.get("approx_cost_for_two") is not None:
        extracted["cost_ambiguous"] = False
    if extracted.get("restaurant_type") is not None:
        extracted["rest_type_ambiguous"] = False

    return extracted


def validate_accumulated_parameters(params: dict, ambiguous_flags: dict = None) -> dict:
    """
    Validate whether all 6 required business-analysis inputs are available:
    1. location
    2. primary_cuisine (cuisine)
    3. restaurant_type
    4. approx_cost_for_two
    5. online_order (has_online_order)
    6. book_table (has_table_booking)
    """
    missing_inputs = []
    ambiguous_inputs = []
    amb_flags = ambiguous_flags or {}

    p = params or {}

    if not p.get("location"):
        missing_inputs.append("location")

    if not p.get("primary_cuisine"):
        missing_inputs.append("cuisine")

    if amb_flags.get("rest_type_ambiguous"):
        ambiguous_inputs.append("restaurant_type")
    elif not p.get("restaurant_type"):
        missing_inputs.append("restaurant_type")

    if amb_flags.get("cost_ambiguous"):
        ambiguous_inputs.append("approx_costfor_two_people")
    elif p.get("approx_cost_for_two") is None:
        missing_inputs.append("approx_costfor_two_people")

    if p.get("online_order") is None:
        missing_inputs.append("has_online_order")

    if p.get("book_table") is None:
        missing_inputs.append("has_table_booking")

    is_valid = (len(missing_inputs) == 0) and (len(ambiguous_inputs) == 0)

    return {
        "is_valid": is_valid,
        "missing_inputs": missing_inputs,
        "ambiguous_inputs": ambiguous_inputs,
    }


def build_missing_inputs_response(missing_inputs: list, ambiguous_inputs: list) -> str:
    """
    Build a polite, concise conversational response asking ONLY for missing or ambiguous inputs.
    Does NOT ask for information already provided.
    """
    if "approx_costfor_two_people" in ambiguous_inputs:
        return (
            "What approximate cost for two should I use?\n"
            "For example: ₹500, ₹800, ₹1,200."
        )

    if "restaurant_type" in ambiguous_inputs:
        return (
            "What restaurant type should I use?\n"
            "For example: Casual Dining, Fine Dining, Café, or QSR."
        )

    field_labels = {
        "location": "• Location — e.g. Whitefield, Koramangala, Indiranagar",
        "cuisine": "• Cuisine — e.g. North Indian, Italian, Chinese, Café",
        "restaurant_type": "• Restaurant type — e.g. Casual Dining, Fine Dining, Café, QSR",
        "approx_costfor_two_people": "• Cost for two — e.g. ₹1,200",
        "has_online_order": "• Online ordering — Yes or No?",
        "has_table_booking": "• Table booking — Yes or No?",
    }

    bullets = [field_labels[f] for f in missing_inputs if f in field_labels]

    if len(bullets) == 1:
        return f"One detail is still needed:\n\n{bullets[0]}"
    else:
        items_str = "\n".join(bullets)
        return (
            f"Sure! I can analyze this. I just need a few more details:\n\n"
            f"{items_str}\n\n"
            f"Once you provide these, I'll run the complete analysis."
        )


def derive_cost_band(cost: float) -> str:
    if cost < 400:
        return "Low"
    elif cost < 1000:
        return "Medium"
    elif cost < 2000:
        return "Upper-Mid"
    return "High"

# -----------------------------------------------------------------------------
# AUTHENTICATION ENDPOINTS
# -----------------------------------------------------------------------------

@app.post("/api/auth/register")
@limiter.limit("10/minute")
def register_user(request: Request, req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account with secure Argon2id password hashing.
    Enforces strong input validation and prevents user enumeration via generic responses.
    """
    clean_username = req.username.strip()
    clean_email = req.email.strip().lower()

    validate_username(clean_username)
    validate_email(clean_email)
    validate_password_strength(req.password)

    # Check for existing user or email
    existing_user = db.query(User).filter(
        (User.username == clean_username) | (User.email == clean_email)
    ).first()
    if existing_user:
        # Generic error message to prevent username/email enumeration
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. An account with these credentials cannot be created.",
        )

    hashed_pw = hash_password(req.password)
    user_id = str(uuid.uuid4())
    new_user = User(
        id=user_id,
        username=clean_username,
        email=clean_email,
        hashed_password=hashed_pw,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.id, "username": new_user.username})
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }
    }


@app.post("/api/auth/login")
@limiter.limit("10/minute")
def login_user(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with Argon2id and issue JWT.
    Enforces generic error message to prevent user enumeration.
    """
    identifier = req.username_or_email.strip()
    user = db.query(User).filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    # Always run password verification (or dummy verification) to prevent timing-based enumeration attacks
    dummy_hash = "$argon2id$v=19$m=65536,t=2,p=1$c29tZXNhbHQ1Njc4OTAxMg$O7uV+XkQJcZ3n+pB7j3O3hE3+9kQZ1uV+XkQJcZ3n+o"
    target_hash = user.hashed_password if (user and user.hashed_password) else dummy_hash
    is_valid = verify_password(req.password, target_hash)

    if not user or not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id, "username": user.username})
    return {
        "status": "success",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }


@app.get("/api/auth/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve currently authenticated user profile."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


# -----------------------------------------------------------------------------
# API ENDPOINTS
# -----------------------------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "BizAdvisor Backend API",
        "orchestration": "Deterministic multi-stage pipeline + Gemini",
        "ml_model": "Random Forest + SHAP",
        "timestamp": datetime.datetime.now().isoformat()
    }


@app.post("/api/analyze")
@limiter.limit("20/minute")
def run_analysis_endpoint(
    request: Request,
    req: AnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Run full business analysis for given explicit structured parameters.
    Uses the genuine ADK runtime (falls back to Python pipeline if Gemini unavailable).
    Requires authenticated user and rate-limited to 20 requests/minute.
    """
    try:
        cost_band = derive_cost_band(req.approx_cost_for_two)
        search_q = req.search_query or f"{req.primary_cuisine} restaurants in {req.location}"

        analysis_output = run_analysis_via_adk(
            location=req.location,
            search_query=search_q,
            online_order=1 if req.online_order else 0,
            book_table=1 if req.book_table else 0,
            approx_cost=req.approx_cost_for_two,
            cost_band=cost_band,
            primary_cuisine=req.primary_cuisine,
            cuisine_count=req.cuisine_count,
            rest_type=req.restaurant_type,
            radius_km=req.radius_km
        )

        return {
            "status": "success",
            "orchestration": analysis_output.pop("_orchestration", "unknown"),
            "parameters": req.dict(),
            "analysis": analysis_output
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis execution error: {str(e)}")


def isolate_scenario_parameters(
    user_message: str,
    prev_params: dict,
    candidate_params: Optional[dict] = None
) -> Tuple[dict, list, list]:
    """
    Deterministically isolate scenario parameters for a FOLLOW_UP_SCENARIO.

    STRICT RULES:
    1. baseline prev_params MUST be preserved (never mutated).
    2. Only fields explicitly mentioned/changed in user_message may change.
    3. Gemini candidate_params are used ONLY for explicitly mentioned fields.
    4. Returns (scenario_params, rich_changed_fields, changed_field_keys).
    """
    import copy
    import re

    # Baseline deepcopy — NO MUTATION of prev_params
    scenario_params = copy.deepcopy(prev_params)
    msg_lower = user_message.lower()

    changed_field_keys = []
    rich_changed_fields = []

    # 1. PRICE / COST FIELD
    price_keywords = ["price", "cost", "charge", "rate", "budget", "₹", "rs", "inr", "rupees", "for two"]
    has_price_mention = (
        any(k in msg_lower for k in price_keywords) or
        bool(re.search(r'\b\d{3,5}\b', msg_lower))
    )

    if has_price_mention:
        old_cost = float(prev_params.get("approx_cost_for_two", 800.0))
        new_cost = None

        cost_match = re.search(r'(?:₹|rs\.?\s*|inr\s*|cost\s+(?:for\s+two\s+|of\s+|for\s+)?|price\s+(?:is\s+|to\s+|at\s+)?|to\s+₹?|at\s+₹?)(\d{2,5})', msg_lower)
        if not cost_match:
            cost_match = re.search(r'\b(\d{3,5})\b', msg_lower)

        if cost_match:
            try:
                new_cost = float(cost_match.group(1))
            except ValueError:
                pass

        if new_cost is None and candidate_params:
            cand_cost = candidate_params.get("approx_cost_for_two") or candidate_params.get("cost_for_two") or candidate_params.get("cost")
            if cand_cost is not None:
                try:
                    new_cost = float(cand_cost)
                except ValueError:
                    pass

        if new_cost is not None:
            scenario_params["approx_cost_for_two"] = new_cost
            scenario_params["cost_band"] = derive_cost_band(new_cost)
            changed_field_keys.append("approx_cost_for_two")

            delta = round(new_cost - old_cost, 2)
            pct = round(((new_cost - old_cost) / old_cost) * 100, 1) if old_cost > 0 else 0.0
            rich_changed_fields.append({
                "field": "approx_cost_for_two",
                "display_name": "Cost for Two",
                "old_value": old_cost,
                "new_value": new_cost,
                "unit": "₹",
                "delta": delta,
                "pct_change": pct
            })

    # 2. CUISINE FIELD
    cuisine_keywords = [
        "italian", "chinese", "north indian", "south indian", "japanese", "korean",
        "continental", "biryani", "cafe", "bakery", "dessert", "ice cream", "icecream",
        "gelato", "burger", "pizza", "sushi", "waffle", "brownie", "shake", "milkshake",
        "smoothie", "mexican", "thai", "kebab", "mughlai", "seafood", "asian", "mediterranean",
        "cuisine", "food"
    ]
    has_cuisine_mention = any(ck in msg_lower for ck in cuisine_keywords)

    if has_cuisine_mention:
        old_cuisine = prev_params.get("primary_cuisine", "North Indian")
        new_cuisine = None

        if candidate_params:
            cand_cuis = candidate_params.get("primary_cuisine") or candidate_params.get("cuisine")
            if cand_cuis and cand_cuis.strip().lower() != old_cuisine.lower():
                new_cuisine = cand_cuis.strip().title()

        if not new_cuisine:
            cuis_map = {
                "italian": "Italian", "chinese": "Chinese", "north indian": "North Indian",
                "south indian": "South Indian", "japanese": "Japanese", "korean": "Korean",
                "biryani": "Biryani", "cafe": "Cafe", "bakery": "Bakery", "dessert": "Dessert",
                "ice cream": "Ice Cream", "icecream": "Ice Cream", "burger": "Burger",
                "pizza": "Italian", "sushi": "Japanese", "continental": "Continental",
                "mexican": "Mexican", "thai": "Thai"
            }
            for ck, cname in cuis_map.items():
                if ck in msg_lower:
                    new_cuisine = cname
                    break

        if new_cuisine and new_cuisine.lower() != old_cuisine.lower():
            scenario_params["primary_cuisine"] = new_cuisine
            location = scenario_params.get("location", "Bengaluru")
            scenario_params["search_query"] = f"{new_cuisine} restaurant in {location}"
            changed_field_keys.append("primary_cuisine")

            rich_changed_fields.append({
                "field": "primary_cuisine",
                "display_name": "Cuisine",
                "old_value": old_cuisine,
                "new_value": new_cuisine,
                "unit": None,
                "delta": None,
                "pct_change": None
            })

    # 3. LOCATION FIELD
    location_keywords = [
        "whitefield", "indiranagar", "koramangala", "hsr", "jayanagar", "bellandur",
        "mg road", "brookefield", "marathahalli", "jp nagar", "electronic city",
        "sarjapur", "btm", "malleshwaram", "rajajinagar", "yelahanka", "hebbal",
        "ulsoor", "banaswadi", "location", "place", "area", "shifted", "moved"
    ]
    has_location_mention = any(lk in msg_lower for lk in location_keywords)

    if has_location_mention:
        old_location = prev_params.get("location", "Koramangala, Bengaluru")
        new_location = None

        if candidate_params:
            cand_loc = candidate_params.get("location")
            if cand_loc and cand_loc.strip().lower() != old_location.lower():
                new_location = cand_loc.strip()

        if not new_location:
            loc_map = [
                ("hsr", "HSR Layout, Bengaluru"),
                ("indiranagar", "Indiranagar, Bengaluru"),
                ("whitefield", "Whitefield, Bengaluru"),
                ("jayanagar", "Jayanagar, Bengaluru"),
                ("mg road", "MG Road, Bengaluru"),
                ("brookefield", "Brookefield, Bengaluru"),
                ("bellandur", "Bellandur, Bengaluru"),
                ("jp nagar", "JP Nagar, Bengaluru"),
                ("marathahalli", "Marathahalli, Bengaluru"),
                ("electronic city", "Electronic City, Bengaluru"),
                ("sarjapur", "Sarjapur Road, Bengaluru"),
                ("btm", "BTM Layout, Bengaluru"),
                ("malleshwaram", "Malleshwaram, Bengaluru"),
                ("rajajinagar", "Rajajinagar, Bengaluru"),
                ("yelahanka", "Yelahanka, Bengaluru"),
                ("hebbal", "Hebbal, Bengaluru"),
                ("ulsoor", "Ulsoor, Bengaluru"),
                ("banaswadi", "Banaswadi, Bengaluru"),
                ("koramangala", "Koramangala, Bengaluru")
            ]
            for lkey, lname in loc_map:
                if lkey in msg_lower:
                    new_location = lname
                    break

        if new_location and new_location.lower() != old_location.lower():
            scenario_params["location"] = new_location
            cuisine = scenario_params.get("primary_cuisine", "Restaurant")
            scenario_params["search_query"] = f"{cuisine} restaurant in {new_location}"
            changed_field_keys.append("location")

            rich_changed_fields.append({
                "field": "location",
                "display_name": "Location",
                "old_value": old_location,
                "new_value": new_location,
                "unit": None,
                "delta": None,
                "pct_change": None
            })

    # 4. ONLINE ORDER FIELD
    if any(w in msg_lower for w in ["online order", "online delivery", "delivery", "swiggy", "zomato"]):
        old_val = prev_params.get("online_order", True)
        new_val = False if ("no " in msg_lower or "disable" in msg_lower or "stop" in msg_lower or "without" in msg_lower) else True
        if new_val != old_val:
            scenario_params["online_order"] = new_val
            changed_field_keys.append("online_order")
            rich_changed_fields.append({
                "field": "online_order",
                "display_name": "Online Ordering",
                "old_value": "Yes" if old_val else "No",
                "new_value": "Yes" if new_val else "No",
                "unit": None,
                "delta": None,
                "pct_change": None
            })

    # 5. TABLE BOOKING FIELD
    if any(w in msg_lower for w in ["table booking", "book table", "reservation"]):
        old_val = prev_params.get("book_table", False)
        new_val = False if ("no " in msg_lower or "disable" in msg_lower or "stop" in msg_lower or "without" in msg_lower) else True
        if new_val != old_val:
            scenario_params["book_table"] = new_val
            changed_field_keys.append("book_table")
            rich_changed_fields.append({
                "field": "book_table",
                "display_name": "Table Booking",
                "old_value": "Yes" if old_val else "No",
                "new_value": "Yes" if new_val else "No",
                "unit": None,
                "delta": None,
                "pct_change": None
            })

    # 6. CUSTOMERS PER DAY
    if any(w in msg_lower for w in ["customer", "customers", "guest", "guests", "footfall", "diners"]):
        old_cpd = float(prev_params.get("customers_per_day", 100.0))
        m_cpd = re.search(r'(?:(\d+(?:\.\d+)?)\s*(?:customers|guests|footfall|diners))|(?:(?:customers|guests|footfall|diners)\D{0,10}(\d+(?:\.\d+)?))', msg_lower)
        new_cpd = None
        if m_cpd:
            try:
                val_str = m_cpd.group(1) or m_cpd.group(2)
                if val_str:
                    new_cpd = float(val_str)
            except ValueError:
                pass
        if new_cpd is not None and new_cpd != old_cpd:
            scenario_params["customers_per_day"] = new_cpd
            changed_field_keys.append("customers_per_day")
            rich_changed_fields.append({
                "field": "customers_per_day",
                "display_name": "Daily Customers",
                "old_value": old_cpd,
                "new_value": new_cpd,
                "unit": "/day",
                "delta": round(new_cpd - old_cpd, 1),
                "pct_change": round(((new_cpd - old_cpd) / old_cpd) * 100, 1) if old_cpd > 0 else 0.0
            })

    # 7. RENT
    if "rent" in msg_lower or "lease" in msg_lower:
        old_rent = float(prev_params.get("rent", 60000.0))
        m_rent = re.search(r'(?:rent|lease)\D{0,15}(?:₹|rs\.?\s*)?(\d+(?:\.\d+)?\s*(?:lakh|lakhs|l|k|thousand)?)', msg_lower)
        if not m_rent:
            m_rent = re.search(r'(?:₹|rs\.?\s*)?(\d+(?:\.\d+)?\s*(?:lakh|lakhs|l|k|thousand)?)\s*(?:rent|lease)', msg_lower)
        new_rent = None
        if m_rent:
            raw_str = m_rent.group(1).lower().strip()
            m_num = re.search(r'(\d+(?:\.\d+)?)\s*(lakh|lakhs|l|k|thousand)?', raw_str)
            if m_num:
                v = float(m_num.group(1))
                u = m_num.group(2)
                if u in ["lakh", "lakhs", "l"]:
                    v *= 100000.0
                elif u in ["k", "thousand"]:
                    v *= 1000.0
                new_rent = v
        if new_rent is not None and new_rent != old_rent:
            scenario_params["rent"] = new_rent
            changed_field_keys.append("rent")
            rich_changed_fields.append({
                "field": "rent",
                "display_name": "Monthly Rent",
                "old_value": f"₹{int(old_rent):,}",
                "new_value": f"₹{int(new_rent):,}",
                "unit": "₹",
                "delta": round(new_rent - old_rent, 2),
                "pct_change": round(((new_rent - old_rent) / old_rent) * 100, 1) if old_rent > 0 else 0.0
            })

    return scenario_params, rich_changed_fields, changed_field_keys


def parse_user_query_and_intent(
    user_message: str,
    prev_params: Optional[dict] = None,
    recent_messages: Optional[list] = None,
    has_baseline: bool = False
) -> dict:
    """
    Classify user message intent and extract/merge parameters with session context.
    Intents:
    - CASUAL_QUESTION: General questions, greetings, SHAP, metrics, scores, app concept.
    - INCOMPLETE_IDEA: Vague idea like "I want to open a restaurant" without location/cuisine.
    - FOLLOW_UP_SCENARIO: What-if / scenario change on existing session context.
    - NEW_ANALYSIS: Fresh analysis request with new concept / explicit instruction.
    """
    msg_lower = user_message.lower().strip()
    msg_clean = msg_lower.strip(" .!?👋")

    # Extract user's name if introduced in current message or recent chat history
    user_name = None
    import re
    name_regex = r"\b(?:i['’]?m|im|i\s+am|my\s+name\s+is)\s+([a-zA-Z]+)"
    if recent_messages:
        for m in recent_messages:
            if m.get("role") == "user":
                c_lower = m.get("content", "").lower()
                m_name = re.search(name_regex, c_lower)
                if m_name:
                    user_name = m_name.group(1).title()
                    break

    m_self_intro = re.search(name_regex, msg_lower)
    if not user_name and m_self_intro:
        user_name = m_self_intro.group(1).title()

    # 0. Greetings & Casual conversation check
    greetings = [
        "hey", "hi", "hello", "hii", "heyy", "good morning", "good afternoon", "good evening",
        "what's up", "whatsapp", "how are you", "thanks", "thank you", "okay", "ok", "cool",
        "nice", "great", "awesome", "help", "who are you", "what can you do", "bizadvisor", "bye", "goodbye", "see ya",
        "interesting", "got it", "understood", "sounds good", "perfect", "yep", "yeah"
    ]

    is_greeting = any(msg_clean == g or msg_clean.startswith(g + " ") for g in greetings) or m_self_intro is not None

    if is_greeting:
        name_prefix = f", {user_name}" if user_name else ""
        if "bye" in msg_lower or "goodbye" in msg_lower or "see ya" in msg_lower:
            answer = f"Bye{name_prefix}! 👋 Feel free to come back whenever you want to explore another business idea."
        elif m_self_intro:
            answer = f"Nice to meet you{name_prefix}! 👋 What business idea are you exploring today?"
        elif "thank" in msg_lower:
            answer = f"You're very welcome{name_prefix}! 👋 Let me know if you need any further business analysis."
        elif "how can u help" in msg_lower or "how can you help" in msg_lower or "what can you do" in msg_lower:
            answer = f"Hi{name_prefix}! BizAdvisor combines historical Zomato location benchmarks, Random Forest ML performance predictions, and real-time Google Places competitor discovery to guide restaurant investment decisions."
        elif "cool" in msg_lower or "nice" in msg_lower or "great" in msg_lower or "awesome" in msg_lower or "interesting" in msg_lower:
            answer = f"Glad you find it helpful{name_prefix}! Let me know if you want to test any what-if scenarios or adjust your concept."
        else:
            answer = f"Hey{name_prefix}! 👋 What business idea are you exploring? Share your restaurant concept, location, or target cost, or ask me any question about market metrics!"

        return {
            "intent": "CASUAL_QUESTION",
            "casual_answer": answer,
            "params": prev_params,
            "changed_fields": []
        }

    # 1. Casual question / informational prompt check
    question_starters = [
        "what is", "what does", "what are", "how does", "how do", "how is", "why is", "why are",
        "explain", "tell me", "define", "meaning of", "what means", "can you explain",
        "who is", "where does", "is there", "do you have"
    ]
    domain_terms = [
        "shap", "random forest", "opportunity score", "google places", "location context",
        "median cost", "online order", "table booking", "competitor", "prediction", "ml model",
        "zomato", "bizadvisor", "cost band", "diversity", "feature", "score", "metric"
    ]

    is_question = (
        any(msg_lower.startswith(q) for q in question_starters) or
        "?" in user_message or
        any(term in msg_lower for term in domain_terms)
    )

    # Extended location list — covers all common Bengaluru neighbourhoods
    _known_locations = [
        "whitefield", "indiranagar", "koramangala", "hsr", "jayanagar", "bellandur",
        "mg road", "bengaluru", "bangalore", "brookefield", "marathahalli", "jp nagar",
        "electronic city", "sarjapur", "btm", "malleshwaram", "rajajinagar",
        "yelahanka", "hebbal", "ulsoor", "banaswadi", "bannerghatta", "kengeri",
        "banashankari", "devanahalli", "old airport road", "victoria layout",
    ]
    has_loc = any(loc in msg_lower for loc in _known_locations)

    # Extended cuisine / food-type list — includes dessert, ice cream, shake, etc.
    _known_cuisines = [
        "japanese", "korean", "italian", "chinese", "biryani", "north indian",
        "south indian", "cafe", "pizza", "burger", "sushi", "ice cream", "icecream",
        "gelato", "dessert", "waffle", "brownie", "bakery", "shake", "milkshake",
        "smoothie", "continental", "mexican", "thai", "kebab", "mughlai", "seafood",
        "outlet", "parlor", "parlour", "sweet",
    ]
    has_cuis = any(cuis in msg_lower for cuis in _known_cuisines)

    # Extended cost detection — handles "cost for two 450", "₹450", "rs 450", etc.
    import re as _re
    has_cost = bool(
        any(k in msg_lower for k in ["₹", "rs", "inr", "cost of", "cost for", "price of", "per two", "budget"]) or
        _re.search(r'cost\s+(?:for\s+(?:two|2)\s+)?\d{3,5}', msg_lower)
    )

    # --- DIAGNOSTIC LOGGING (temporary, request-scoped) ---
    print(f"[ROUTING] has_loc={has_loc} | has_cuis={has_cuis} | has_cost={has_cost}")

    # If prompt specifies explicit business idea (e.g. location + cuisine/cost) or explicit what-if scenario, it's not a casual question
    has_explicit_analysis = (has_loc and (has_cuis or has_cost)) or "new analysis" in msg_lower or "fresh analysis" in msg_lower
    is_what_if_scenario = "what if" in msg_lower or "how about" in msg_lower or "reduce" in msg_lower or "increase" in msg_lower or "switch to" in msg_lower or "change" in msg_lower

    if is_question and not has_explicit_analysis and not is_what_if_scenario and not (prev_params and not has_baseline):
        answer = None
        if "shap" in msg_lower:
            answer = (
                "SHAP (SHapley Additive exPlanations) measures how much each input feature pushed the model "
                "toward or away from a prediction class. It explains **model behavior**, not physical causation — "
                "meaning it shows what the Random Forest model prioritized when evaluating your concept."
            )
        elif "random forest" in msg_lower or "rf" in msg_lower:
            answer = (
                "Random Forest is an ensemble machine learning model trained on historical restaurant data. "
                "It combines multiple decision trees to evaluate location density, pricing, cuisine demand, "
                "and feature flags to predict business performance success probabilities."
            )
        elif "google places" in msg_lower or "place" in msg_lower:
            answer = (
                "Google Places API provides real-time geospatial data on existing competitors within a 3km radius, "
                "including live star ratings, total user reviews, and competitor categories."
            )
        elif "opportunity" in msg_lower:
            answer = (
                "The Opportunity Score (0–100) synthesizes three main pillars: historical location demand, "
                "ML success probability, and local competition density. Higher scores reflect favorable overall positioning."
            )
        elif "competitor" in msg_lower or "competition" in msg_lower:
            answer = (
                "Competitor density is retrieved via real-time Google Places queries within a 3km radius. "
                "A higher competitor count means a more crowded market, which may require stronger differentiation."
            )
        elif "location" in msg_lower or "rate" in msg_lower:
            answer = (
                "Location benchmarks analyze historical Zomato data for your area, including total restaurant count, "
                "median cost for two, online ordering adoption rates, and table booking rates."
            )
        elif "break even" in msg_lower or "break-even" in msg_lower or "breakeven" in msg_lower:
            bep_val = None
            if prev_params:
                from src.finance.simulator import simulate_financials
                aov = prev_params.get("average_order_value") or (prev_params.get("approx_cost_for_two", 800.0) / 2.0)
                fin_d = simulate_financials(
                    customers_per_day=prev_params.get("customers_per_day", 100.0),
                    average_order_value=aov,
                    rent=prev_params.get("rent", 60000.0),
                    staff_cost=prev_params.get("staff_cost", 50000.0),
                    food_cost_percent=prev_params.get("food_cost_percent", 30.0),
                    utilities=prev_params.get("utilities", 15000.0),
                    marketing=prev_params.get("marketing", 10000.0),
                    other_expenses=prev_params.get("other_expenses", 5000.0),
                    working_days=prev_params.get("working_days", 30.0),
                )
                bep_val = fin_d.get("break_even_customers_per_day")
                bep_target = fin_d.get("break_even_target_customers_per_day")
                bep_achievable = fin_d.get("break_even_achievable", True)

            if bep_achievable and bep_val is not None:
                target_str = f"{bep_target}" if bep_target is not None else f"{math.ceil(bep_val)}"
                bep_str = f"{round(bep_val, 1)}"
                answer = (
                    f"Based on your modeled monthly operating costs, you need an estimated **{target_str} customers per day** "
                    f"({bep_str} exact) to cover fixed and variable operating expenses.\n\n"
                    f"*Estimated customers required per day to cover modeled operating costs. This is an assumption-based estimate, not a guaranteed real-world requirement.*"
                )
            else:
                answer = (
                    "Break-even cannot be achieved under the current assumptions because variable costs equal or exceed 100% of revenue, "
                    "leaving no contribution margin to cover fixed operating costs."
                )
        elif "how can u help" in msg_lower or "how can you help" in msg_lower or "what can you do" in msg_lower:
            name_str = f" {user_name}" if user_name else ""
            answer = f"Hi{name_str}! BizAdvisor combines historical Zomato location benchmarks, Random Forest ML performance predictions, and real-time Google Places competitor discovery to guide restaurant investment decisions."
        else:
            answer = (
                "BizAdvisor combines historical Zomato location benchmarks, Random Forest ML performance predictions, "
                "and real-time Google Places competitor discovery to guide restaurant investment decisions."
            )
        return {
            "intent": "CASUAL_QUESTION",
            "casual_answer": answer,
            "params": prev_params,
            "changed_fields": []
        }

    # 2. Check for explicit new analysis command
    is_explicit_new = "new analysis" in msg_lower or "start new" in msg_lower or "fresh analysis" in msg_lower

    # 3. Check for incomplete business idea (vague prompt without location/cuisine details)
    incomplete_patterns = [
        "i want to open a restaurant", "i want to start a business", "i want to open a cafe",
        "restaurant idea", "open a restaurant", "i want to start a restaurant", "i want to open a new restaurant"
    ]
    if (not prev_params and not is_explicit_new and not has_explicit_analysis) or any(msg_clean == pat for pat in incomplete_patterns):
        if any(msg_clean == pat for pat in incomplete_patterns) or (not prev_params and msg_clean.startswith("i want to open a restaurant")):
            return {
                "intent": "INCOMPLETE_IDEA",
                "clarification_prompt": (
                    "Sounds like a great project! Which location in Bengaluru are you considering (e.g. Whitefield, Indiranagar, Koramangala), "
                    "and what cuisine or restaurant concept do you have in mind?"
                ),
                "params": None,
                "changed_fields": []
            }

    # Use Groq / LLM API if available for context parsing
    api_key = os.getenv("PRIMARY_LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            from src.agent.llm_config import PRIMARY_MODEL_NAME
            import litellm

            formatted_chat_history = ""
            if recent_messages:
                formatted_chat_history = "\n".join([
                    f"{m['role'].capitalize()}: {m['content']}"
                    for m in recent_messages[-10:] if m.get("content")
                ])

            prev_params_json = json.dumps(prev_params) if prev_params else "None"
            prompt = f"""
You are BizAdvisor, a strict JSON-only parameter extractor for restaurant business analysis.

Existing Business Parameters (the current baseline session):
{prev_params_json}

Recent Conversation History:
{formatted_chat_history if formatted_chat_history else "None"}

Current User Message: "{user_message}"

Return ONLY a valid JSON object with EXACTLY these keys:
  "intent": one of "NEW_ANALYSIS", "FOLLOW_UP_SCENARIO", "INCOMPLETE_IDEA", "CASUAL_QUESTION"
  "casual_answer": string or null
  "clarification_prompt": string or null
  "changed_fields": array of strings — ONLY the field names that the user explicitly changed
  "params": object or null

STRICT RULES:
1. CASUAL_QUESTION: user is greeting, saying thanks/bye, asking a definition, or chatting. Set casual_answer, params=existing params, changed_fields=[].
2. FOLLOW_UP_SCENARIO: user modifies ONE or more specific fields on the existing concept.
   - Copy ALL fields from Existing Business Parameters unchanged.
   - ONLY update the fields the user explicitly mentioned changing.
   - List those updated field names in changed_fields.
   - DO NOT invent or modify any field the user did not explicitly mention.
   - Examples:
     "What if price is ₹1500?" → changed_fields=["approx_cost_for_two"], cuisine/location/etc unchanged.
     "What if I switch to Italian?" → changed_fields=["primary_cuisine"], cost/location/etc unchanged.
     "Italian at ₹1500" → changed_fields=["primary_cuisine","approx_cost_for_two"].
3. NEW_ANALYSIS: user introduces a completely new concept with a different location or entirely new idea.
4. INCOMPLETE_IDEA: user mentions a restaurant idea but missing key details like location or cuisine.
5. No markdown backticks. Return raw JSON only.
"""
            response = litellm.completion(
                model=PRIMARY_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = response.choices[0].message.content.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(raw_text)

            # ── CRITICAL DEFENSIVE SCENARIO ISOLATION ──────────────────────────────
            if (
                (parsed.get("intent") == "FOLLOW_UP_SCENARIO" or is_what_if_scenario)
                and prev_params
                and has_baseline
            ):
                cand_params = parsed.get("params") if isinstance(parsed, dict) else None
                scen_params, rich_cf, cf_keys = isolate_scenario_parameters(user_message, prev_params, cand_params)
                print(f"[SCENARIO ENFORCEMENT] changed_fields={cf_keys} | enforced params applied")
                return {
                    "intent": "FOLLOW_UP_SCENARIO",
                    "changed_fields": rich_cf,
                    "changed_field_keys": cf_keys,
                    "params": scen_params
                }
            elif (parsed.get("intent") in ["FOLLOW_UP_SCENARIO", "CASUAL_QUESTION"]) and prev_params and not has_baseline and not is_what_if_scenario:
                fresh = parse_user_query(user_message)
                if any(fresh.get(k) is not None for k in ["approx_cost_for_two", "restaurant_type", "online_order", "book_table", "location", "primary_cuisine"]):
                    parsed["intent"] = "NEW_ANALYSIS"
                    merged = dict(prev_params)
                    merged.update({k: v for k, v in fresh.items() if v is not None})
                    parsed["params"] = merged
                    parsed["changed_fields"] = list(fresh.keys())
            elif "params" in parsed and parsed["params"]:
                cost_raw = parsed["params"].get("approx_cost_for_two")
                if cost_raw is not None:
                    try:
                        cost_num = float(cost_raw)
                        parsed["params"]["approx_cost_for_two"] = cost_num
                        parsed["params"]["cost_band"] = derive_cost_band(cost_num)
                    except (TypeError, ValueError):
                        pass
                else:
                    parsed["params"]["approx_cost_for_two"] = None
            return parsed
        except Exception as e:
            print(f"[QueryParser Warning] Gemini intent parsing error: {e}. Falling back to rule parser.")

    # Rule-based fallback parser for follow-up scenarios
    if is_what_if_scenario or (prev_params and has_baseline and not is_explicit_new):
        scen_params, rich_cf, cf_keys = isolate_scenario_parameters(user_message, prev_params or {}, None)
        print(f"[ROUTING] intent=FOLLOW_UP_SCENARIO | changed_field_keys={cf_keys}")
        print(f"[ROUTING] parameters={json.dumps(scen_params, ensure_ascii=False)}")
        return {
            "intent": "FOLLOW_UP_SCENARIO",
            "changed_fields": rich_cf,
            "changed_field_keys": cf_keys,
            "params": scen_params
        }

    # Execute NEW_ANALYSIS if explicit parameters exist or if accumulating missing inputs prior to baseline
    if has_explicit_analysis or (has_loc and (has_cuis or has_cost)) or (prev_params and not has_baseline):
        fresh = parse_user_query(user_message)
        if prev_params and not is_explicit_new:
            merged = dict(prev_params)
            merged.update({k: v for k, v in fresh.items() if v is not None})
            result_params = merged
        else:
            result_params = fresh
        print(f"[ROUTING] intent=NEW_ANALYSIS")
        print(f"[ROUTING] parameters={json.dumps(result_params, ensure_ascii=False)}")
        return {
            "intent": "NEW_ANALYSIS",
            "changed_fields": list(fresh.keys()),
            "params": result_params
        }

    # Fallback for vague inputs without explicit location & cuisine parameters: DO NOT RUN NEW_ANALYSIS!
    if any(p in msg_clean for p in ["restaurant", "cafe", "business", "food", "dine", "eat", "open", "start"]):
        return {
            "intent": "INCOMPLETE_IDEA",
            "clarification_prompt": (
                "Sounds like a great project! Which location in Bengaluru are you considering (e.g. Whitefield, Indiranagar, Koramangala), "
                "and what cuisine or restaurant concept do you have in mind?"
            ),
            "params": None,
            "changed_fields": []
        }

    name_str = f", {user_name}" if user_name else ""
    return {
        "intent": "CASUAL_QUESTION",
        "casual_answer": f"Hey{name_str}! 👋 I'm BizAdvisor, your AI business analyst. Ask me any question about restaurant market data or ML predictions, or share your restaurant concept, location, and target cost to run a full analysis!",
        "params": prev_params,
        "changed_fields": []
    }


@app.post("/api/chat")
@limiter.limit("30/minute")
def chat_endpoint(
    request: Request,
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Chat interaction endpoint.
    Strictly validates that ALL 6 required business-analysis inputs are available:
    1. location
    2. cuisine
    3. restaurant_type
    4. approx_cost_for_two
    5. online_order
    6. book_table

    If any input is missing or ambiguous:
    - DO NOT run RandomForest, SHAP, Competition, Opportunity, Financial analysis.
    - Ask the user ONLY for the missing/ambiguous details using a clear checklist.

    Enforces that conversation belongs to current_user.
    """
    db = SessionLocal()
    try:
        # If session_id provided, verify ownership
        if req.session_id:
            existing_conv = db.query(Conversation).filter(Conversation.id == req.session_id).first()
            if existing_conv and existing_conv.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have permission to access or modify this conversation.",
                )

        # Ensure active session corresponds to an existing, committed conversation row belonging to current_user
        conv = get_or_create_conversation(
            db,
            session_id=req.session_id,
            default_title="New Analysis",
            user_id=current_user.id,
        )
        session_id = conv.id

        prev_params = conv.parameters_json if conv.parameters_json else None
        prev_analysis = conv.analysis_json if conv.analysis_json else None
        existing_messages = [m.to_dict() for m in conv.messages]

        # Parse message & intent using context and recent conversation history
        has_baseline = (prev_analysis is not None)
        parsed_result = parse_user_query_and_intent(req.message, prev_params, recent_messages=existing_messages, has_baseline=has_baseline)
        intent = parsed_result.get("intent", "NEW_ANALYSIS")

        # ---------------------------------------------------------------------
        # INTENT 1: CASUAL QUESTION
        # ---------------------------------------------------------------------
        if intent == "CASUAL_QUESTION":
            ai_message = parsed_result.get("casual_answer") or (
                "SHAP (SHapley Additive exPlanations) measures how much each input feature pushed the model "
                "toward or away from a prediction class."
            )
            save_chat_turn(
                db,
                session_id=session_id,
                user_message=req.message,
                ai_message=ai_message,
                mode="casual",
                parameters=prev_params,
                user_id=current_user.id,
            )
            return {
                "session_id": session_id,
                "intent": "CASUAL_QUESTION",
                "mode": "casual",
                "ai_message": ai_message,
                "parameters": prev_params,
                "analysis": None,
                "scenario_comparison": None,
                "timestamp": datetime.datetime.now().isoformat()
            }

        # ---------------------------------------------------------------------
        # PARAMETER EXTRACTION & STATE ACCUMULATION
        # ---------------------------------------------------------------------
        extracted_p = dict(parsed_result.get("params")) if parsed_result.get("params") else parse_user_query(req.message)
        rule_p = extract_business_parameters(req.message)
        for k, v in rule_p.items():
            if extracted_p.get(k) is None and v is not None:
                extracted_p[k] = v

        accumulated_params = dict(prev_params) if prev_params else {
            "location": None,
            "primary_cuisine": None,
            "restaurant_type": None,
            "approx_cost_for_two": None,
            "online_order": None,
            "book_table": None,
            "cuisine_count": 2,
            "radius_km": 3.0,
        }
        for k in ["location", "primary_cuisine", "restaurant_type", "approx_cost_for_two", "online_order", "book_table"]:
            if extracted_p.get(k) is not None:
                accumulated_params[k] = extracted_p[k]

        # Normalize location string canonical format
        if accumulated_params.get("location"):
            accumulated_params["location"] = normalize_location(accumulated_params["location"])

        amb_flags = {
            "cost_ambiguous": extracted_p.get("cost_ambiguous", False),
            "rest_type_ambiguous": extracted_p.get("rest_type_ambiguous", False),
        }

        # Standalone short-answer parsing (e.g. user answered "Yes" / "Table booking yes" to previous missing inputs prompt)
        msg_lower_clean = req.message.lower().strip(" .!?")
        if prev_params:
            prev_val = validate_accumulated_parameters(prev_params)
            missing_bools = [f for f in ["has_online_order", "has_table_booking"] if f in prev_val["missing_inputs"]]
            if len(missing_bools) == 1:
                target_f = missing_bools[0]
                key = "online_order" if target_f == "has_online_order" else "book_table"
                if accumulated_params.get(key) is None:
                    if msg_lower_clean in ("yes", "yeah", "yep", "true", "1") or "yes" in msg_lower_clean.split():
                        accumulated_params[key] = True
                    elif msg_lower_clean in ("no", "nah", "nope", "false", "0") or "no" in msg_lower_clean.split():
                        accumulated_params[key] = False

        # Validate accumulated parameters
        validation = validate_accumulated_parameters(accumulated_params, amb_flags)

        msg_lower = req.message.lower()
        is_what_if_request = (intent == "FOLLOW_UP_SCENARIO") or any(w in msg_lower for w in ["what if", "how about", "increase", "reduce", "switch to", "change cost", "change price"])

        # ---------------------------------------------------------------------
        # WHAT-IF WITHOUT BASELINE CHECK
        # ---------------------------------------------------------------------
        if is_what_if_request and prev_analysis is None:
            missing_prompt = build_missing_inputs_response(validation["missing_inputs"], validation["ambiguous_inputs"])
            ai_message = f"A baseline business analysis must be completed before running What-If scenarios.\n\n{missing_prompt}"

            save_chat_turn(
                db,
                session_id=session_id,
                user_message=req.message,
                ai_message=ai_message,
                mode="casual",
                title="Incomplete Analysis",
                parameters=accumulated_params,
                user_id=current_user.id,
            )

            return {
                "session_id": session_id,
                "intent": "NEEDS_INPUT",
                "status": "needs_input",
                "mode": "casual",
                "ai_message": ai_message,
                "parameters": accumulated_params,
                "analysis": None,
                "scenario_comparison": None,
                "timestamp": datetime.datetime.now().isoformat()
            }

        # ---------------------------------------------------------------------
        # MISSING / AMBIGUOUS INPUTS CHECK (BEFORE RUNNING ANY ANALYSIS TOOLS)
        # ---------------------------------------------------------------------
        if not validation["is_valid"]:
            ai_message = build_missing_inputs_response(validation["missing_inputs"], validation["ambiguous_inputs"])

            save_chat_turn(
                db,
                session_id=session_id,
                user_message=req.message,
                ai_message=ai_message,
                mode="casual",
                title="Incomplete Analysis",
                parameters=accumulated_params,
                user_id=current_user.id,
            )

            return {
                "session_id": session_id,
                "intent": "NEEDS_INPUT",
                "status": "needs_input",
                "mode": "casual",
                "ai_message": ai_message,
                "parameters": accumulated_params,
                "missing_inputs": validation["missing_inputs"],
                "analysis": None,
                "scenario_comparison": None,
                "timestamp": datetime.datetime.now().isoformat()
            }


        # ---------------------------------------------------------------------
        # ALL 6 REQUIRED INPUTS PRESENT: EXECUTE FULL ANALYSIS OR WHAT-IF
        # ---------------------------------------------------------------------
        is_scenario = is_what_if_request and (prev_analysis is not None)
        rich_changed_fields = []
        if is_scenario:
            params, rich_changed_fields, changed_field_keys = isolate_scenario_parameters(req.message, prev_params, extracted_p)
            accumulated_params = params
        else:
            params = accumulated_params

        cost = float(params["approx_cost_for_two"])
        cost_band = derive_cost_band(cost)
        location = str(params["location"])
        cuisine = str(params["primary_cuisine"])
        rest_type = str(params["restaurant_type"])
        online_order = 1 if params["online_order"] else 0
        book_table = 1 if params["book_table"] else 0
        search_q = f"{cuisine} restaurant in {location}"

        changed_fields = rich_changed_fields

        scenario_comparison_data = None

        if is_scenario and prev_analysis and not any(f in changed_fields for f in ["location"]):
            # Price / Cuisine / Feature change only — REUSE location context & Google Places!
            loc_res = prev_analysis.get("location_result", {})
            comp_res = prev_analysis.get("competition_result", {})

            from src.ml.predictor import predict_business_performance
            from src.agent.opportunity_agent import opportunity_analysis_tool

            perf_res = predict_business_performance(
                online_order=online_order,
                book_table=book_table,
                approx_costfor_two_people=cost,
                cost_band=cost_band,
                location=location.split(",")[0].strip(),
                primary_cuisine=cuisine,
                cuisine_count=params.get("cuisine_count", 2),
                primary_rest_type=rest_type,
                historical_restaurant_count=loc_res.get("historical_restaurant_count", 1000),
                location_median_cost=loc_res.get("location_median_cost", 500.0),
                location_online_order_rate=loc_res.get("location_online_order_rate", 0.6),
                location_book_table_rate=loc_res.get("location_book_table_rate", 0.15),
                location_cuisine_diversity=loc_res.get("location_cuisine_diversity", 10),
                location_business_type_diversity=loc_res.get("location_business_type_diversity", 5)
            )

            prob_dict = perf_res.get("probabilities", {})
            comp_summary = comp_res.get("competition_summary", {})
            opp_res = opportunity_analysis_tool(
                probabilities=prob_dict,
                model_classes=list(prob_dict.keys()),
                competition_summary=comp_summary
            )

            analysis = {
                "location_result": loc_res,
                "performance_result": perf_res,
                "competition_result": comp_res,
                "opportunity_result": opp_res
            }

            base_score = round(float(prev_analysis.get("opportunity_result", {}).get("opportunity_score", {}).get("score", 0.0)), 2)
            scen_score = round(float(opp_res.get("opportunity_score", {}).get("score", 0.0)), 2)
            score_delta = round(scen_score - base_score, 2)

            base_high_prob = round((prev_analysis.get("performance_result", {}).get("probabilities", {}).get("High", 0.0)) * 100, 1)
            scen_high_prob = round((perf_res.get("probabilities", {}).get("High", 0.0)) * 100, 1)
            prob_delta = round(scen_high_prob - base_high_prob, 1)

            base_perf_score = round(float(prev_analysis.get("opportunity_result", {}).get("historical_performance", {}).get("score", 0.0)), 2)
            scen_perf_score = round(float(opp_res.get("historical_performance", {}).get("score", 0.0)), 2)
            perf_score_delta = round(scen_perf_score - base_perf_score, 2)

            base_comp_score = round(float(prev_analysis.get("opportunity_result", {}).get("competition_strength", {}).get("score", 0.0)), 2)
            scen_comp_score = round(float(opp_res.get("competition_strength", {}).get("score", 0.0)), 2)
            comp_score_delta = round(scen_comp_score - base_comp_score, 2)

            b_cost = float(prev_params.get("approx_cost_for_two", 800.0))
            s_cost = float(cost)
            cost_delta = round(s_cost - b_cost, 2)

            # Explanations using opportunity.py formula
            if perf_score_delta == 0 and comp_score_delta == 0:
                perf_explanation = f"Performance score remained identical at {base_perf_score:.2f}."
                comp_explanation = f"Competition score remained identical at {base_comp_score:.2f}."
                overall_reason = f"Both performance and competition components are identical to baseline. Opportunity Score remains at {base_score:.2f}."
            elif comp_score_delta == 0:
                dir_str = "decrease" if perf_score_delta < 0 else "increase"
                perf_explanation = f"Performance score shifted from {base_perf_score:.2f} to {scen_perf_score:.2f} ({perf_score_delta:+.2f} pts)."
                comp_explanation = f"Competition score remained unchanged at {base_comp_score:.2f}."
                overall_reason = f"The competition component remained unchanged ({base_comp_score:.2f}). The {dir_str} in Opportunity Score (from {base_score:.2f} to {scen_score:.2f}) came entirely from the performance component."
            elif perf_score_delta == 0:
                dir_str = "decrease" if comp_score_delta > 0 else "increase"
                perf_explanation = f"Performance score remained unchanged at {base_perf_score:.2f}."
                comp_explanation = f"Competition score shifted from {base_comp_score:.2f} to {scen_comp_score:.2f} ({comp_score_delta:+.2f} pts)."
                overall_reason = f"The performance component remained unchanged ({base_perf_score:.2f}). The Opportunity Score shifted from {base_score:.2f} to {scen_score:.2f} due to changes in competition intensity."
            else:
                perf_explanation = f"Performance score shifted from {base_perf_score:.2f} to {scen_perf_score:.2f} ({perf_score_delta:+.2f} pts)."
                comp_explanation = f"Competition score shifted from {base_comp_score:.2f} to {scen_comp_score:.2f} ({comp_score_delta:+.2f} pts)."
                overall_reason = f"Both performance ({base_perf_score:.2f} → {scen_perf_score:.2f}) and competition ({base_comp_score:.2f} → {scen_comp_score:.2f}) components contributed to the Opportunity Score shift ({base_score:.2f} → {scen_score:.2f})."

            summary_notes = []
            if score_delta > 0:
                summary_notes.append(f"Opportunity score improved by +{score_delta} points ({base_score} → {scen_score}).")
            elif score_delta < 0:
                summary_notes.append(f"Opportunity score decreased by {score_delta} points ({base_score} → {scen_score}).")
            else:
                summary_notes.append(f"Opportunity score remained constant at {base_score}.")

            if prob_delta != 0:
                sign = "+" if prob_delta > 0 else ""
                summary_notes.append(f"High-performance probability shifted by {sign}{prob_delta}% points.")

            from src.ml.explainer import compare_shap_drivers

            shap_analysis = compare_shap_drivers(
                base_params=prev_params,
                scen_params=params,
                loc_ctx=loc_res,
                target_class="High",
                top_n=5
            )

            model_driver_changes = shap_analysis.get("model_driver_changes", [])
            prob_explanation_dict = shap_analysis.get("probability_explanation", {})

            opportunity_breakdown_dict = {
                "baseline_performance": base_perf_score,
                "scenario_performance": scen_perf_score,
                "performance_delta": perf_score_delta,
                "baseline_competition": base_comp_score,
                "scenario_competition": scen_comp_score,
                "competition_delta": comp_score_delta,
                "baseline_opportunity": base_score,
                "scenario_opportunity": scen_score,
                "opportunity_delta": score_delta,
                "summary": overall_reason
            }

            from src.finance.simulator import simulate_financials
            from src.analysis.what_if import compare_financial_scenarios, describe_financial_changes

            b_fin_params = {
                "customers_per_day": prev_params.get("customers_per_day", 100.0),
                "average_order_value": prev_params.get("average_order_value") or (prev_params.get("approx_cost_for_two", 800.0) / 2.0),
                "rent": prev_params.get("rent", 60000.0),
                "staff_cost": prev_params.get("staff_cost", 50000.0),
                "food_cost_percent": prev_params.get("food_cost_percent", 30.0),
                "utilities": prev_params.get("utilities", 15000.0),
                "marketing": prev_params.get("marketing", 10000.0),
                "other_expenses": prev_params.get("other_expenses", 5000.0),
                "working_days": prev_params.get("working_days", 30.0),
            }

            s_fin_params = {
                "customers_per_day": params.get("customers_per_day", b_fin_params["customers_per_day"]),
                "average_order_value": params.get("average_order_value") or (params.get("approx_cost_for_two", 800.0) / 2.0),
                "rent": params.get("rent", b_fin_params["rent"]),
                "staff_cost": params.get("staff_cost", b_fin_params["staff_cost"]),
                "food_cost_percent": params.get("food_cost_percent", b_fin_params["food_cost_percent"]),
                "utilities": params.get("utilities", b_fin_params["utilities"]),
                "marketing": params.get("marketing", b_fin_params["marketing"]),
                "other_expenses": params.get("other_expenses", b_fin_params["other_expenses"]),
                "working_days": params.get("working_days", b_fin_params["working_days"]),
            }

            fin_comp = compare_financial_scenarios(b_fin_params, s_fin_params)
            fin_comp["statements"] = describe_financial_changes(fin_comp)

            scen_fin_res = simulate_financials(**s_fin_params)
            analysis["financial_result"] = scen_fin_res
            analysis["financial"] = scen_fin_res

            scenario_comparison_data = {
                "changed_fields": changed_fields,
                "baseline": {
                    "parameters": prev_params,
                    "analysis": prev_analysis,
                    "location": prev_params.get("location"),
                    "cuisine": prev_params.get("primary_cuisine"),
                    "cost_for_two": b_cost,
                    "prediction": prev_analysis.get("performance_result", {}).get("prediction", "N/A"),
                    "probabilities": prev_analysis.get("performance_result", {}).get("probabilities", {}),
                    "high_probability": base_high_prob,
                    "opportunity_score": base_score,
                    "performance_score": base_perf_score,
                    "competition_score": base_comp_score
                },
                "scenario": {
                    "parameters": params,
                    "analysis": analysis,
                    "location": location,
                    "cuisine": cuisine,
                    "cost_for_two": cost,
                    "prediction": perf_res.get("prediction", "N/A"),
                    "probabilities": prob_dict,
                    "high_probability": scen_high_prob,
                    "opportunity_score": scen_score,
                    "performance_score": scen_perf_score,
                    "competition_score": scen_comp_score
                },
                "comparison": {
                    "base_score": base_score,
                    "scenario_score": scen_score,
                    "score_delta": score_delta,
                    "base_high_prob": base_high_prob,
                    "scenario_high_prob": scen_high_prob,
                    "prob_delta_pct": prob_delta,
                    "base_prediction": prev_analysis.get("performance_result", {}).get("prediction", "N/A"),
                    "scenario_prediction": perf_res.get("prediction", "N/A"),
                    "summary_notes": summary_notes
                },
                "deltas": {
                    "cost": cost_delta,
                    "high_probability": prob_delta,
                    "opportunity_score": score_delta,
                    "performance_score": perf_score_delta,
                    "competition_score": comp_score_delta
                },
                "explanation": {
                    "performance_change": perf_explanation,
                    "competition_change": comp_explanation,
                    "overall_reason": overall_reason
                },
                "model_driver_changes": model_driver_changes,
                "probability_explanation": prob_explanation_dict,
                "opportunity_breakdown": opportunity_breakdown_dict,
                "financial_comparison": fin_comp
            }

            cost_str = f"₹{int(cost):,}"
            score_delta_str = f"+{score_delta}" if score_delta > 0 else str(score_delta)

            cf_list = changed_fields
            cf_names = [cf.get("display_name", cf.get("field")) if isinstance(cf, dict) else str(cf) for cf in cf_list]
            cf_str = ", ".join(cf_names) if cf_names else "parameters"

            ai_message = (
                f"Sure — I've updated **{cf_str}** while keeping the rest of your baseline concept in **{location}** unchanged.\n\n"
                f"Recalculated model prediction: **{perf_res['prediction']}** probability of success with an Opportunity Score of **{scen_score}/100** ({score_delta_str} pts vs baseline)."
            )

            title = f"{cuisine} Restaurant · {location.split(',')[0]}"
            user_msg_obj = {"role": "user", "content": req.message, "timestamp": datetime.datetime.now().isoformat()}
            ai_msg_obj = {
                "role": "assistant",
                "content": ai_message,
                "mode": "scenario",
                "analysis": None,
                "scenarioComparison": scenario_comparison_data,
                "parameters": params,
                "timestamp": datetime.datetime.now().isoformat()
            }
            save_chat_turn(
                db,
                session_id=session_id,
                user_message=req.message,
                ai_message=ai_message,
                mode="scenario",
                title=title,
                parameters=params,
                scenario_comparison=scenario_comparison_data,
                user_id=current_user.id,
            )

            return {
                "session_id": session_id,
                "intent": "FOLLOW_UP_SCENARIO",
                "mode": "scenario",
                "title": title,
                "ai_message": ai_message,
                "parameters": params,
                "analysis": None,
                "scenario_comparison": scenario_comparison_data,
                "timestamp": datetime.datetime.now().isoformat()
            }

        else:
            # Full business analysis execution
            analysis = run_analysis_via_adk(
                location=location,
                search_query=search_q,
                online_order=online_order,
                book_table=book_table,
                approx_cost=cost,
                cost_band=cost_band,
                primary_cuisine=cuisine,
                cuisine_count=params.get("cuisine_count", 2),
                rest_type=rest_type,
                radius_km=3.0,
                session_id=session_id,
            )
            _orchestration_mode = analysis.pop("_orchestration", "unknown")

            comp_res = analysis.get("competition_result", {})
            comp_count = len(comp_res.get("competitors", [])) or comp_res.get("competition_summary", {}).get("competitor_count_retrieved", 0)
            comp_res["competitor_count"] = comp_count

            pred_class = analysis["performance_result"]["prediction"]
            opp_score = analysis["opportunity_result"]["opportunity_score"]["score"]

            # Inject backend-generated Business Takeaway into analysis
            # so the frontend displays and reads the EXACT same text.
            analysis["business_takeaway"] = build_business_takeaway(
                location=location,
                cuisine=cuisine,
                rest_type=rest_type,
                analysis=analysis,
            )

            ai_message = (
                f"Nice — let's test that **{cuisine}** concept in **{location}** with an estimated cost of **₹{int(cost):,} for two**.\n\n"
                f"Our Random Forest model predicts a **{pred_class}** probability of success with an Opportunity Score of **{opp_score}/100** "
                f"and **{comp_count} direct competitors** nearby."
            )

            title = f"{cuisine} Restaurant · {location.split(',')[0]}"
            save_chat_turn(
                db,
                session_id=session_id,
                user_message=req.message,
                ai_message=ai_message,
                mode="full",
                title=title,
                parameters=params,
                analysis=analysis,
                user_id=current_user.id,
            )

            return {
                "session_id": session_id,
                "intent": intent,
                "mode": "full",
                "title": title,
                "ai_message": ai_message,
                "parameters": params,
                "analysis": analysis,
                "scenario_comparison": None,
                "timestamp": datetime.datetime.now().isoformat()
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error running business analysis chat: {str(e)}")
    finally:
        db.close()



@app.post("/api/scenario")
@limiter.limit("20/minute")
def create_scenario_endpoint(
    request: Request,
    req: ScenarioRequest,
    current_user: User = Depends(get_current_user),
):
    """
    What-If / Scenario Comparison Endpoint.
    Compares original baseline parameters against new scenario parameters using backend ML predictor & opportunity agent.
    Returns side-by-side comparison data and metric deltas.
    Validates session ownership if session_id is provided.
    """
    try:
        # If session_id provided, verify that the session belongs to the current user
        if req.session_id:
            s_check_db = SessionLocal()
            try:
                existing_conv = s_check_db.query(Conversation).filter(Conversation.id == req.session_id).first()
                if existing_conv and existing_conv.user_id != current_user.id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: You cannot run scenarios on another user's conversation.",
                    )
            finally:
                s_check_db.close()

        base_p = req.baseline_params
        scen_p = req.scenario_params

        # Run baseline analysis
        base_cost = base_p.get("approx_cost_for_two", 800.0)
        base_band = derive_cost_band(base_cost)
        base_loc = base_p.get("location", "Koramangala, Bengaluru")
        base_cuis = base_p.get("primary_cuisine", "Japanese")

        base_full = run_analysis_via_adk(
            location=base_loc,
            search_query=base_p.get("search_query") or f"{base_cuis} restaurant in {base_loc}",
            online_order=1 if base_p.get("online_order", True) else 0,
            book_table=1 if base_p.get("book_table", True) else 0,
            approx_cost=base_cost,
            cost_band=base_band,
            primary_cuisine=base_cuis,
            cuisine_count=base_p.get("cuisine_count", 2),
            rest_type=base_p.get("restaurant_type", "Casual Dining")
        )
        base_full.pop("_orchestration", None)

        # Run scenario analysis
        scen_cost = scen_p.get("approx_cost_for_two", 800.0)
        scen_band = derive_cost_band(scen_cost)
        scen_loc = scen_p.get("location", base_loc)
        scen_cuis = scen_p.get("primary_cuisine", base_cuis)

        scen_full = run_analysis_via_adk(
            location=scen_loc,
            search_query=scen_p.get("search_query") or f"{scen_cuis} restaurant in {scen_loc}",
            online_order=1 if scen_p.get("online_order", True) else 0,
            book_table=1 if scen_p.get("book_table", True) else 0,
            approx_cost=scen_cost,
            cost_band=scen_band,
            primary_cuisine=scen_cuis,
            cuisine_count=scen_p.get("cuisine_count", 2),
            rest_type=scen_p.get("restaurant_type", "Casual Dining")
        )
        scen_full.pop("_orchestration", None)

        # Extract score & probability deltas
        base_score = base_full["opportunity_result"]["opportunity_score"]["score"]
        scen_score = scen_full["opportunity_result"]["opportunity_score"]["score"]
        score_diff = round(scen_score - base_score, 1)

        base_high_prob = base_full["performance_result"]["probabilities"].get("High", 0.0)
        scen_high_prob = scen_full["performance_result"]["probabilities"].get("High", 0.0)
        prob_diff = round((scen_high_prob - base_high_prob) * 100, 1)

        summary_bullets = []
        if score_diff > 0:
            summary_bullets.append(f"Opportunity score increased by +{score_diff} points ({base_score} → {scen_score}).")
        elif score_diff < 0:
            summary_bullets.append(f"Opportunity score decreased by {score_diff} points ({base_score} → {scen_score}).")
        else:
            summary_bullets.append(f"Opportunity score remains constant at {base_score}.")

        if prob_diff > 0:
            summary_bullets.append(f"High-performance ML probability improved by +{prob_diff}% points.")
        elif prob_diff < 0:
            summary_bullets.append(f"High-performance ML probability decreased by {prob_diff}% points.")

        if base_cost != scen_cost:
            cost_diff = scen_cost - base_cost
            sign = "+" if cost_diff > 0 else ""
            summary_bullets.append(f"Cost for two adjusted by {sign}₹{int(cost_diff)} (₹{int(base_cost)} → ₹{int(scen_cost)}).")

        scenario_comparison_data = {
            "status": "success",
            "baseline": {
                "parameters": base_p,
                "analysis": base_full
            },
            "scenario": {
                "parameters": scen_p,
                "analysis": scen_full
            },
            "comparison": {
                "base_score": base_score,
                "scenario_score": scen_score,
                "score_delta": score_diff,
                "base_high_prob": round(base_high_prob * 100, 1),
                "scenario_high_prob": round(scen_high_prob * 100, 1),
                "prob_delta_pct": prob_diff,
                "base_prediction": base_full["performance_result"]["prediction"],
                "scenario_prediction": scen_full["performance_result"]["prediction"],
                "summary_notes": summary_bullets
            }
        }

        # If session_id provided, persist scenario comparison to MySQL conversations & messages scoped to current_user
        if req.session_id:
            s_db = SessionLocal()
            try:
                save_chat_turn(
                    s_db,
                    session_id=req.session_id,
                    user_message=f"What-If Scenario: {scen_loc} ({scen_cuis}) - Cost ₹{int(scen_cost)}",
                    ai_message=f"**Scenario Comparison Executed:** Comparing original baseline against updated inputs for **{scen_loc}**.",
                    mode="scenario",
                    parameters=scen_p,
                    analysis=scen_full,
                    scenario_comparison=scenario_comparison_data,
                    user_id=current_user.id,
                )
            except Exception as pe:
                print(f"[Scenario Persistence Warning] Could not save scenario: {pe}")
            finally:
                s_db.close()

        return scenario_comparison_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing scenario comparison: {str(e)}")


@app.post("/api/financial/simulate")
@limiter.limit("60/minute")
def simulate_financials_endpoint(
    request: Request,
    req: FinancialSimulateRequest,
):
    """
    Deterministic financial simulation endpoint.
    Recalculates monthly revenue, itemized fixed costs, total operating expenses,
    estimated operating profit, operating profit margin, and break-even customer targets.
    """
    try:
        from src.finance.simulator import simulate_financials
        return simulate_financials(
            customers_per_day=req.customers_per_day,
            average_order_value=req.average_order_value,
            rent=req.rent,
            staff_cost=req.staff_cost,
            food_cost_percent=req.food_cost_percent,
            utilities=req.utilities,
            marketing=req.marketing,
            other_expenses=req.other_expenses,
            working_days=req.working_days,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@app.get("/api/history")
@limiter.limit("60/minute")
def get_history_endpoint(
    request: Request,
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve past analysis conversations list for the left sidebar history.
    Strictly isolated: returns ONLY conversations belonging to the authenticated user.
    """
    db = SessionLocal()
    try:
        history_list = get_conversation_list(db, search_query=search, user_id=current_user.id)
        return {"history": history_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")
    finally:
        db.close()


@app.get("/api/history/{session_id}")
@limiter.limit("60/minute")
def get_history_item_endpoint(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve full session detail and message trajectory for a single history item.
    Enforces that the conversation belongs to the authenticated user.
    """
    db = SessionLocal()
    try:
        detail = get_conversation_detail(db, session_id=session_id, user_id=current_user.id)
        if not detail:
            # Check if it exists for another user to return 403 or 404
            other_user_conv = db.query(Conversation).filter(Conversation.id == session_id).first()
            if other_user_conv and other_user_conv.user_id != current_user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You do not have permission to view this conversation.")
            raise HTTPException(status_code=404, detail="Analysis session not found")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading session detail: {str(e)}")
    finally:
        db.close()


@app.delete("/api/history/{session_id}")
@limiter.limit("30/minute")
def delete_history_item(
    request: Request,
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a history conversation and its cascaded messages.
    Enforces that the conversation belongs to the authenticated user.
    """
    db = SessionLocal()
    try:
        # Check if conversation exists and belongs to someone else
        existing_conv = db.query(Conversation).filter(Conversation.id == session_id).first()
        if existing_conv and existing_conv.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: You cannot delete another user's conversation.")

        success = delete_conversation(db, session_id=session_id, user_id=current_user.id)
        if not success:
            return {"status": "not_found", "session_id": session_id}
        return {"status": "deleted", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting history item: {str(e)}")
    finally:
        db.close()


# -----------------------------------------------------------------------------
# SERVE STATIC FRONTEND IN PRODUCTION (IF DIST EXISTS)
# -----------------------------------------------------------------------------

dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
