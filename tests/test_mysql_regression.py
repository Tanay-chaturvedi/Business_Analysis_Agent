"""
tests/test_mysql_regression.py
==============================
Regression tests for MySQL conversation history handling in BizAdvisor.

Verifies:
1. New chats commit a `conversations` row to MySQL before messages and analysis are persisted.
2. Existing chats update metadata/analysis and append messages without StaleDataError.
3. Invalid or deleted session IDs are handled safely without crashing or losing messages.
4. Direct reproduction of `StaleDataError` (UPDATE statement on table 'conversations' expected to update 1 row(s); 0 were matched)
   and verification that `save_chat_turn` recovers cleanly, recreating the conversation row and saving messages.
5. FastAPI /api/chat endpoint works seamlessly for new chats, existing chats, and stale/deleted session IDs.
"""

import os
import sys
import uuid
import pytest
from datetime import datetime
from sqlalchemy.orm.exc import StaleDataError

# Set path to project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database import (
    SessionLocal,
    Conversation,
    Message,
    get_or_create_conversation,
    save_chat_turn,
    get_conversation_detail,
    delete_conversation,
)
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_new_chat_commits_conversation_before_messages():
    """Verify that a new conversation is committed to MySQL before its messages are persisted."""
    db = SessionLocal()
    session_id = f"test-new-{uuid.uuid4()}"
    try:
        # get_or_create_conversation commits immediately
        conv = get_or_create_conversation(db, session_id=session_id, default_title="Fresh Conversation")
        assert conv.id == session_id

        # Verify it exists in a separate session/connection (i.e. committed)
        verify_db = SessionLocal()
        found = verify_db.query(Conversation).filter(Conversation.id == session_id).first()
        assert found is not None, "Conversation was not committed to MySQL before subsequent operations"
        verify_db.close()

        # Now save chat turn
        updated_conv = save_chat_turn(
            db,
            session_id=session_id,
            user_message="Hello BizAdvisor",
            ai_message="Welcome! How can I help you?",
            mode="casual",
            title="Fresh Conversation",
        )
        assert updated_conv.id == session_id

        # Verify messages persisted
        detail = get_conversation_detail(db, session_id)
        assert detail is not None
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["content"] == "Hello BizAdvisor"
        assert detail["messages"][1]["content"] == "Welcome! How can I help you?"
    finally:
        delete_conversation(db, session_id)
        db.close()


def test_existing_chat_updates_cleanly():
    """Verify that follow-up turns in an existing conversation update state without errors."""
    db = SessionLocal()
    session_id = f"test-existing-{uuid.uuid4()}"
    try:
        # Turn 1
        save_chat_turn(
            db,
            session_id=session_id,
            user_message="Turn 1 question",
            ai_message="Turn 1 answer",
            mode="casual",
            title="Multi-Turn Chat",
            parameters={"location": "Indiranagar, Bengaluru"},
        )

        # Turn 2
        save_chat_turn(
            db,
            session_id=session_id,
            user_message="Turn 2 question",
            ai_message="Turn 2 answer",
            mode="casual",
            parameters={"location": "Indiranagar, Bengaluru", "primary_cuisine": "Italian"},
        )

        detail = get_conversation_detail(db, session_id)
        assert detail is not None
        assert len(detail["messages"]) == 4
        assert detail["parameters"]["primary_cuisine"] == "Italian"
    finally:
        delete_conversation(db, session_id)
        db.close()


def test_reproduce_and_recover_from_stale_data_error():
    """
    Directly reproduces the error:
    `UPDATE statement on table 'conversations' expected to update 1 row(s); 0 were matched.`
    and verifies that save_chat_turn recovers cleanly without crashing or losing messages.
    """
    db = SessionLocal()
    session_id = f"test-stale-{uuid.uuid4()}"
    try:
        # 1. Create a conversation
        conv = Conversation(
            id=session_id,
            title="Initial Title",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_message_at=datetime.utcnow(),
            parameters_json={},
            analysis_json={},
        )
        db.add(conv)
        db.commit()

        # 2. Simulate concurrent deletion in a separate database session
        delete_session = SessionLocal()
        delete_session.query(Conversation).filter(Conversation.id == session_id).delete()
        delete_session.commit()
        delete_session.close()

        # 3. Call save_chat_turn on the now-deleted conversation ID
        # Under naive update, this would raise:
        # `StaleDataError: UPDATE statement on table 'conversations' expected to update 1 row(s); 0 were matched.`
        recovered_conv = save_chat_turn(
            db,
            session_id=session_id,
            user_message="Message after concurrent delete",
            ai_message="I recovered your conversation safely.",
            mode="casual",
            title="Recovered Session",
        )

        # 4. Verify conversation was recovered and messages are safely stored
        assert recovered_conv is not None
        assert recovered_conv.id == session_id

        detail = get_conversation_detail(db, session_id)
        assert detail is not None
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["content"] == "Message after concurrent delete"
        assert detail["messages"][1]["content"] == "I recovered your conversation safely."
    finally:
        delete_conversation(db, session_id)
        db.close()


def test_api_chat_lifecycle_with_stale_and_new_sessions():
    """Verify FastAPI /api/chat with new session, follow-up, and deleted/invalid session."""
    test_user = f"chat_reg_{uuid.uuid4().hex[:8]}"
    reg_res = client.post("/api/auth/register", json={
        "username": test_user,
        "email": f"{test_user}@example.com",
        "password": "Password123"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. New chat (no session_id)
    res1 = client.post("/api/chat", headers=auth_headers, json={"message": "What is SHAP?"})
    assert res1.status_code == 200
    data1 = res1.json()
    new_session_id = data1["session_id"]
    assert new_session_id is not None
    assert data1["mode"] == "casual"

    # 2. Follow-up message with existing session_id
    res2 = client.post("/api/chat", headers=auth_headers, json={
        "message": "Can you elaborate on random forest?",
        "session_id": new_session_id
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["session_id"] == new_session_id

    # 3. Message with deleted/invalid session_id
    invalid_session_id = f"invalid-session-{uuid.uuid4()}"
    res3 = client.post("/api/chat", headers=auth_headers, json={
        "message": "Hello from a stale session ID",
        "session_id": invalid_session_id
    })
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["session_id"] == invalid_session_id

    # Clean up test sessions
    db = SessionLocal()
    try:
        delete_conversation(db, new_session_id)
        delete_conversation(db, invalid_session_id)
    finally:
        db.close()


if __name__ == "__main__":
    print("Running MySQL conversation history regression tests...")
    test_new_chat_commits_conversation_before_messages()
    print("[PASS] New chat commits conversation before messages")
    test_existing_chat_updates_cleanly()
    print("[PASS] Existing chat updates cleanly across multiple turns")
    test_reproduce_and_recover_from_stale_data_error()
    print("[PASS] StaleDataError reproduction and recovery verified")
    test_api_chat_lifecycle_with_stale_and_new_sessions()
    print("[PASS] /api/chat lifecycle (new, existing, stale/deleted IDs) verified")
    print("\nALL REGRESSION TESTS PASSED SUCCESSFULLY!")
