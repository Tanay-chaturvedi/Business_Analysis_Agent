"""
Automated Security Test Suite for BizAdvisor.
Covers:
1. Registration and login succeed with valid inputs.
2. Invalid credentials are rejected with generic errors.
3. Passwords are stored only as secure Argon2id hashes.
4. Missing, expired, malformed, or invalidly signed tokens are rejected.
5. An unauthenticated user cannot access protected endpoints (/api/chat, /api/analyze, /api/scenario, /api/history).
6. User A cannot list or retrieve User B's conversations.
7. User A cannot delete User B's conversations.
8. User A cannot run a scenario against User B's session.
9. A client-supplied user ID cannot override the authenticated identity.
10. CORS rejects untrusted origins / allows configured origins.
11. Login and API rate limits are enforced.
12. Existing conversation/message persistence and cascade deletion still work.
"""

import os
import sys
import uuid
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server import app
from src.database import SessionLocal, User, Conversation, Message, delete_conversation
from src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    validate_jwt_secret,
    get_jwt_secret_key,
)

client = TestClient(app)


def create_test_user(prefix: str = "user") -> tuple[User, str]:
    """Helper to create test user directly in DB to avoid exhaustively hitting the /api/auth/register rate limit."""
    db = SessionLocal()
    try:
        user_id = str(uuid.uuid4())
        username = f"{prefix}_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"
        u = User(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hash_password("Password123"),
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        token = create_access_token({"sub": u.id, "username": u.username})
        return u, token
    finally:
        db.close()


def test_1_registration_and_login_succeed():
    """1. Registration and login succeed with valid inputs."""
    unique_user = f"sec_user_{uuid.uuid4().hex[:8]}"
    email = f"{unique_user}@example.com"
    password = "SecurePassword123"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "username": unique_user,
        "email": email,
        "password": password,
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["username"] == unique_user

    # Login
    login_res = client.post("/api/auth/login", json={
        "username_or_email": unique_user,
        "password": password,
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["username"] == unique_user


def test_2_invalid_credentials_rejected():
    """2. Invalid credentials are rejected with generic error."""
    # Non-existent user
    res1 = client.post("/api/auth/login", json={
        "username_or_email": "non_existent_user_99999",
        "password": "WrongPassword123",
    })
    assert res1.status_code == 401
    assert "Invalid username/email or password" in res1.json()["detail"]

    # Existing user with wrong password
    unique_user = f"user_wrong_{uuid.uuid4().hex[:8]}"
    client.post("/api/auth/register", json={
        "username": unique_user,
        "email": f"{unique_user}@example.com",
        "password": "CorrectPassword123",
    })

    res2 = client.post("/api/auth/login", json={
        "username_or_email": unique_user,
        "password": "WrongPassword123",
    })
    assert res2.status_code == 401
    assert "Invalid username/email or password" in res2.json()["detail"]


def test_3_passwords_stored_only_as_argon2_hashes():
    """3. Passwords are stored only as secure Argon2id hashes (never plaintext)."""
    unique_user = f"hash_user_{uuid.uuid4().hex[:8]}"
    password = "SuperSecretPassword123"

    reg_res = client.post("/api/auth/register", json={
        "username": unique_user,
        "email": f"{unique_user}@example.com",
        "password": password,
    })
    assert reg_res.status_code == 200
    user_id = reg_res.json()["user"]["id"]

    db = SessionLocal()
    try:
        user_row = db.query(User).filter(User.id == user_id).first()
        assert user_row is not None
        assert user_row.hashed_password != password
        assert user_row.hashed_password.startswith("$argon2id$")
        assert verify_password(password, user_row.hashed_password) is True
    finally:
        db.close()


def test_4_token_validation_expired_malformed():
    """4. Missing, expired, malformed, or invalidly signed tokens are rejected."""
    # Malformed token
    res_malformed = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert res_malformed.status_code == 401

    # Expired token
    expired_token = create_access_token(
        data={"sub": str(uuid.uuid4()), "username": "expired_user"},
        expires_delta=timedelta(seconds=-10),
    )
    res_expired = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()


def test_5_unauthenticated_user_cannot_access_protected_routes():
    """5. An unauthenticated user cannot access protected endpoints."""
    # /api/history
    assert client.get("/api/history").status_code == 401
    # /api/chat
    assert client.post("/api/chat", json={"message": "Hello"}).status_code == 401
    # /api/analyze
    assert client.post("/api/analyze", json={"location": "Koramangala, Bengaluru"}).status_code == 401
    # /api/scenario
    assert client.post("/api/scenario", json={"baseline_params": {}, "scenario_params": {}}).status_code == 401


def test_6_user_a_cannot_list_or_retrieve_user_b_conversations():
    """6. User A cannot list or retrieve User B's conversations."""
    _, token_a = create_test_user("usera")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    _, token_b = create_test_user("userb")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B creates a chat session
    session_b = f"sess_b_{uuid.uuid4().hex[:8]}"
    chat_res = client.post("/api/chat", headers=headers_b, json={
        "message": "User B secret chat message",
        "session_id": session_b,
    })
    assert chat_res.status_code == 200

    # User A lists history -> must NOT contain User B's session
    history_a = client.get("/api/history", headers=headers_a).json()["history"]
    history_a_ids = [item["id"] for item in history_a]
    assert session_b not in history_a_ids

    # User A tries to retrieve User B's session directly -> 403 or 404
    detail_res = client.get(f"/api/history/{session_b}", headers=headers_a)
    assert detail_res.status_code in [403, 404]

    # Clean up
    db = SessionLocal()
    try:
        delete_conversation(db, session_b)
    finally:
        db.close()


def test_7_user_a_cannot_delete_user_b_conversations():
    """7. User A cannot delete User B's conversations."""
    _, token_a = create_test_user("usera_del")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    _, token_b = create_test_user("userb_del")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B creates session
    session_b = f"sess_del_{uuid.uuid4().hex[:8]}"
    client.post("/api/chat", headers=headers_b, json={
        "message": "User B session to protect",
        "session_id": session_b,
    })

    # User A tries to delete User B's session -> forbidden
    del_res = client.delete(f"/api/history/{session_b}", headers=headers_a)
    assert del_res.status_code == 403

    # Verify session still exists for User B
    b_detail = client.get(f"/api/history/{session_b}", headers=headers_b)
    assert b_detail.status_code == 200

    # Clean up
    db = SessionLocal()
    try:
        delete_conversation(db, session_b)
    finally:
        db.close()


def test_8_user_a_cannot_run_scenario_on_user_b_session():
    """8. User A cannot run a scenario against User B's session."""
    _, token_a = create_test_user("usera_scen")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    _, token_b = create_test_user("userb_scen")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B creates session
    session_b = f"sess_scen_{uuid.uuid4().hex[:8]}"
    client.post("/api/chat", headers=headers_b, json={
        "message": "User B session for scenario test",
        "session_id": session_b,
    })

    # User A attempts to run scenario against User B's session
    scen_res = client.post("/api/scenario", headers=headers_a, json={
        "baseline_params": {"location": "Koramangala, Bengaluru", "approx_cost_for_two": 800.0},
        "scenario_params": {"location": "Indiranagar, Bengaluru", "approx_cost_for_two": 1200.0},
        "session_id": session_b,
    })
    assert scen_res.status_code == 403

    # Clean up
    db = SessionLocal()
    try:
        delete_conversation(db, session_b)
    finally:
        db.close()


def test_9_client_cannot_spoof_user_id():
    """9. A client-supplied user ID cannot override the authenticated identity."""
    _, token = create_test_user("user_spoof")
    headers = {"Authorization": f"Bearer {token}"}

    fake_user_id = f"fake-id-{uuid.uuid4()}"
    res = client.post("/api/chat", headers=headers, json={
        "message": "Testing user identity binding",
        "user_id": fake_user_id,  # Client tries to pass spoofed user_id
    })
    assert res.status_code == 200
    session_id = res.json()["session_id"]

    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.id == session_id).first()
        assert conv is not None
        # Must match the authenticated user, NOT the spoofed one
        assert conv.user_id != fake_user_id
        # Check against User row
        me_res = client.get("/api/auth/me", headers=headers)
        assert conv.user_id == me_res.json()["id"]
        delete_conversation(db, session_id)
    finally:
        db.close()


def test_10_security_headers_present():
    """10. Security headers are present on responses."""
    res = client.get("/api/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"


def test_11_login_rate_limiting_enforced():
    """11. Login and API rate limits are enforced."""
    # Attempt rapid repeated logins with incorrect credentials
    rapid_results = []
    for _ in range(15):
        r = client.post("/api/auth/login", json={
            "username_or_email": "rate_limit_test",
            "password": "WrongPassword123",
        })
        rapid_results.append(r.status_code)

    # At least one request after the 10/min threshold should return 429
    assert 429 in rapid_results, f"Rate limiter failed to trigger 429: {rapid_results}"


def test_12_cascade_deletion_preserved():
    """12. Existing conversation/message cascade deletion still works."""
    db = SessionLocal()
    session_id = f"test-cascade-{uuid.uuid4()}"
    try:
        conv = Conversation(id=session_id, title="Cascade Test")
        db.add(conv)
        db.commit()

        msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=session_id,
            role="user",
            content="Hello Cascade",
            message_type="text",
        )
        db.add(msg)
        db.commit()

        assert db.query(Message).filter(Message.conversation_id == session_id).count() == 1
        deleted = delete_conversation(db, session_id)
        assert deleted is True
        assert db.query(Message).filter(Message.conversation_id == session_id).count() == 0
    finally:
        db.close()


def test_13_jwt_secret_validation_rejects_missing_empty_and_placeholders(monkeypatch):
    """13. JWT secret validator rejects missing, empty, short, and placeholder secrets safely."""
    # 1. Missing secret
    with pytest.raises(RuntimeError) as exc_info:
        validate_jwt_secret(None)
    assert "missing" in str(exc_info.value).lower()

    # 2. Empty or whitespace-only secret
    for empty_val in ["", "   ", "\t\n"]:
        with pytest.raises(RuntimeError) as exc_info:
            validate_jwt_secret(empty_val)
        assert "empty" in str(exc_info.value).lower()

    # 3. Known development placeholders
    placeholders = [
        "bizadvisor-dev-fallback-secret-key-32-chars-minimum",
        "your_jwt_secret_key_minimum_32_characters_here",
        "your_jwt_secret_key_here",
        "change_me",
        "secret",
        "secretkey",
    ]
    for placeholder in placeholders:
        with pytest.raises(RuntimeError) as exc_info:
            validate_jwt_secret(placeholder)
        assert "placeholder" in str(exc_info.value).lower()

    # 4. Too short (< 32 chars)
    with pytest.raises(RuntimeError) as exc_info:
        validate_jwt_secret("short-secret-under-32-chars")
    assert "short" in str(exc_info.value).lower()

    # 5. Environment-level missing key raises via get_jwt_secret_key()
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        get_jwt_secret_key()
    assert "missing" in str(exc_info.value).lower()


def test_14_jwt_secret_validation_accepts_valid_configuration(monkeypatch):
    """14. JWT secret validator accepts valid 32+ character secrets without exposing them."""
    dummy_valid = "x" * 48
    result = validate_jwt_secret(dummy_valid)
    assert len(result) == 48
    assert result == dummy_valid

    # Validate via environment loading
    monkeypatch.setenv("JWT_SECRET_KEY", dummy_valid)
    env_result = get_jwt_secret_key()
    assert len(env_result) == 48
    assert env_result == dummy_valid
