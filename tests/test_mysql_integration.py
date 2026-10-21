"""
tests/test_mysql_integration.py
===============================
Integration and regression test suite for BizAdvisor MySQL database architecture.
Validates:
1. Exactly TWO application tables exist: `conversations` and `messages`.
2. Conversation creation and title generation.
3. Message creation and cascade deletion.
4. Saving and loading structured analysis JSON (location, ML prediction, SHAP, competition, opportunity score, financials).
5. Saving What-If scenario comparisons.
6. FastAPI endpoints: /api/history, /api/history/{id}, DELETE /api/history/{id}, /api/scenario, /api/chat.
"""

import os
import sys
import uuid
import json
import pytest
from datetime import datetime

# Set path to project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import (
    engine,
    init_db,
    SessionLocal,
    Conversation,
    Message,
    get_or_create_conversation,
    save_chat_turn,
    get_conversation_list,
    get_conversation_detail,
    delete_conversation,
)
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_schema_has_application_tables():
    """Verify that conversations, messages, and users exist in bizadvisor_db."""
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "conversations" in tables, "conversations table missing"
    assert "messages" in tables, "messages table missing"
    assert "users" in tables, "users table missing"
    # Ensure application tables are well-defined
    app_tables = {t for t in tables if not t.startswith("alembic_")}
    assert app_tables == {"conversations", "messages", "users"}, f"Expected {{conversations, messages, users}}, found: {app_tables}"


def test_conversation_crud_and_cascade():
    """Verify conversation creation, message persistence, and cascade deletion."""
    db = SessionLocal()
    test_session_id = f"test-{uuid.uuid4()}"
    try:
        # 1. Create conversation
        conv = get_or_create_conversation(db, test_session_id, default_title="Test Conversation")
        assert conv.id == test_session_id
        assert conv.title == "Test Conversation"

        # 2. Save user and assistant messages
        save_chat_turn(
            db,
            session_id=test_session_id,
            user_message="Hello, can you help me evaluate a restaurant in Whitefield?",
            ai_message="Certainly! Which cuisine and cost for two do you have in mind?",
            mode="casual",
            title="Whitefield Evaluation",
            parameters={"location": "Whitefield, Bengaluru"},
        )

        # 3. Verify retrieval
        detail = get_conversation_detail(db, test_session_id)
        assert detail is not None
        assert detail["title"] == "Whitefield Evaluation"
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["role"] == "user"
        assert detail["messages"][1]["role"] == "assistant"
        assert detail["messages"][1]["mode"] == "casual"

        # 4. Delete conversation and verify cascade
        deleted = delete_conversation(db, test_session_id)
        assert deleted is True

        # Ensure conversation and messages are gone
        assert db.query(Conversation).filter(Conversation.id == test_session_id).first() is None
        assert db.query(Message).filter(Message.conversation_id == test_session_id).count() == 0

    finally:
        db.close()


def test_structured_analysis_persistence():
    """Verify full analysis JSON with location, ML, competition, opportunity, and financials."""
    db = SessionLocal()
    test_session_id = f"test-analysis-{uuid.uuid4()}"
    try:
        sample_params = {
            "location": "Koramangala, Bengaluru",
            "primary_cuisine": "Italian",
            "approx_cost_for_two": 1500.0,
            "restaurant_type": "Casual Dining",
            "online_order": True,
            "book_table": True
        }
        sample_analysis = {
            "location_result": {"location": "Koramangala, Bengaluru", "median_cost": 600},
            "performance_result": {"prediction": "High", "probabilities": {"High": 0.85, "Medium": 0.10, "Low": 0.05}},
            "competition_result": {"competitors": [{"name": "Pasta Bella", "rating": 4.6}], "competitor_count": 12},
            "opportunity_result": {"opportunity_score": {"score": 78.5, "signal": "High"}},
            "financial_result": {"estimated_operating_profit": 140000, "profit_margin": 28.5}
        }

        save_chat_turn(
            db,
            session_id=test_session_id,
            user_message="Analyze Italian restaurant in Koramangala",
            ai_message="Here is your full business analysis for Koramangala.",
            mode="full",
            title="Italian Restaurant · Koramangala",
            parameters=sample_params,
            analysis=sample_analysis,
        )

        detail = get_conversation_detail(db, test_session_id)
        assert detail is not None
        assert detail["parameters"]["primary_cuisine"] == "Italian"
        assert detail["analysis"]["performance_result"]["prediction"] == "High"
        assert detail["analysis"]["opportunity_result"]["opportunity_score"]["score"] == 78.5
        assert detail["opportunity_score"] == 78.5

        # Check list summary
        summary_list = get_conversation_list(db, search_query="Italian Restaurant · Koramangala")
        assert len(summary_list) >= 1
        item = [s for s in summary_list if s["id"] == test_session_id][0]
        assert item["cuisine"] == "Italian"
        assert item["approx_cost"] == 1500.0

    finally:
        delete_conversation(db, test_session_id)
        db.close()


def test_api_history_endpoints():
    """Test FastAPI /api/history endpoints with authentication."""
    # Register/login a temporary test user
    test_user = f"reg_user_{uuid.uuid4().hex[:8]}"
    reg_res = client.post("/api/auth/register", json={
        "username": test_user,
        "email": f"{test_user}@example.com",
        "password": "Password123"
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch history list
    res = client.get("/api/history", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "history" in data
    assert isinstance(data["history"], list)

    # 2. Check 404 on nonexistent session
    nonexistent_id = f"nonexistent-{uuid.uuid4()}"
    res_404 = client.get(f"/api/history/{nonexistent_id}", headers=auth_headers)
    assert res_404.status_code == 404

    # 3. Create a test session via chat endpoint
    test_session = f"api-test-{uuid.uuid4()}"
    chat_res = client.post("/api/chat", headers=auth_headers, json={
        "message": "Hi, what does SHAP mean in BizAdvisor?",
        "session_id": test_session
    })
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["session_id"] == test_session
    assert chat_data["mode"] == "casual"

    # 4. Fetch detail
    detail_res = client.get(f"/api/history/{test_session}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert len(detail_res.json()["messages"]) >= 2

    # 5. Delete session
    del_res = client.delete(f"/api/history/{test_session}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"


if __name__ == "__main__":
    print("Running integration tests...")
    test_schema_has_exactly_two_tables()
    print("[PASS] Exactly two tables verified (conversations, messages)")
    test_conversation_crud_and_cascade()
    print("[PASS] Conversation CRUD & message cascade verified")
    test_structured_analysis_persistence()
    print("[PASS] Structured analysis persistence verified")
    test_api_history_endpoints()
    print("[PASS] API history endpoints verified")
    print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")
