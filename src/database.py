"""
src/database.py
================
SQLAlchemy MySQL Database Engine and Models for BizAdvisor.
Strictly restricted to TWO application tables:
1. `conversations`
2. `messages`

Configured via environment variables (.env) with connection pooling,
proper session lifecycles, and cascade handling.
"""

import os
import uuid
import json
import logging
from urllib.parse import quote_plus
from datetime import datetime, timedelta, timezone
from typing import Generator, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    func,
    text,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    Session,
)
from sqlalchemy.orm.exc import StaleDataError

load_dotenv()
logger = logging.getLogger(__name__)

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "bizadvisor_db")

encoded_password = quote_plus(MYSQL_PASSWORD)
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

# Robust Connection Pool Configuration
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# -----------------------------------------------------------------------------
# TABLE: users
# -----------------------------------------------------------------------------
class User(Base):
    """
    Stores authenticated user accounts for BizAdvisor.
    Each user owns their personal conversation history and What-If scenarios.
    """
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# -----------------------------------------------------------------------------
# TABLE 1: conversations
# -----------------------------------------------------------------------------
class Conversation(Base):
    """
    Stores one record for each business analysis chat conversation.
    Contains overall metadata, latest parameters, and latest structured analysis.
    """
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False, default="New Analysis")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Stores current business analysis parameters (location, cuisine, cost, etc.)
    parameters_json = Column(JSON, nullable=True)

    # Stores latest complete structured BizAdvisor analysis result
    # (location_result, performance_result, competition_result, opportunity_result, financial_result, etc.)
    analysis_json = Column(JSON, nullable=True)

    # Relationship to user
    user = relationship("User", back_populates="conversations")

    # Relationship to messages
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    __table_args__ = (
        Index("idx_conversations_updated_at", "updated_at"),
        Index("idx_conversations_last_message_at", "last_message_at"),
    )

    def to_summary_dict(self) -> Dict[str, Any]:
        """Summary dict for the sidebar list."""
        params = self.parameters_json or {}
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                params = {}

        analysis = self.analysis_json or {}
        if isinstance(analysis, str):
            try:
                analysis = json.loads(analysis)
            except Exception:
                analysis = {}

        opp_score = None
        opp_res = analysis.get("opportunity_result") or {}
        if isinstance(opp_res, dict):
            opp_score = opp_res.get("opportunity_score", {}).get("score")

        pred_class = None
        perf_res = analysis.get("performance_result") or {}
        if isinstance(perf_res, dict):
            pred_class = perf_res.get("prediction")

        approx_cost = params.get("approx_cost_for_two") or params.get("approx_costfor_two_people")

        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "location": params.get("location"),
            "cuisine": params.get("primary_cuisine"),
            "approx_cost": approx_cost,
            "prediction": pred_class,
            "opportunity_score": opp_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }

    def to_detail_dict(self) -> Dict[str, Any]:
        """Full detail dict including parsed messages and analysis."""
        summary = self.to_summary_dict()
        summary["user_id"] = self.user_id
        summary["parameters"] = self.parameters_json or {}
        summary["analysis"] = self.analysis_json or {}
        summary["messages"] = [m.to_dict() for m in self.messages]
        return summary


# -----------------------------------------------------------------------------
# TABLE 2: messages
# -----------------------------------------------------------------------------
class Message(Base):
    """
    Stores every individual user and assistant message for a conversation.
    """
    __tablename__ = "messages"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(
        String(64),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # 'user', 'assistant'
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False, default="text")  # 'text', 'analysis', 'scenario', 'casual', 'needs_input'

    # Rich payload for assistant messages: {mode, analysis, scenarioComparison, parameters}
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_conv_created", "conversation_id", "created_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        meta = self.metadata_json or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}

        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "mode": meta.get("mode", self.message_type),
            "message_type": self.message_type,
            "analysis": meta.get("analysis"),
            "scenarioComparison": meta.get("scenarioComparison"),
            "parameters": meta.get("parameters"),
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }


# -----------------------------------------------------------------------------
# DB Initialization & Session Dependency
# -----------------------------------------------------------------------------
def init_db():
    """Create the 2 MySQL tables if they do not exist."""
    # Ensure database exists
    try:
        raw_conn = engine.raw_connection()
        raw_conn.close()
    except Exception as e:
        logger.warning(f"Could not connect directly with target database: {e}. Attempting database creation...")
        temp_url = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}:{MYSQL_PORT}/?charset=utf8mb4"
        temp_engine = create_engine(temp_url)
        with temp_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            conn.commit()
        temp_engine.dispose()

    Base.metadata.create_all(bind=engine)
    logger.info("MySQL database initialized successfully with 2 tables: conversations, messages.")


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------------------
# High-Level Service Helpers for FastAPI
# -----------------------------------------------------------------------------
def get_or_create_conversation(
    db: Session,
    session_id: Optional[str] = None,
    default_title: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Conversation:
    """
    Retrieve existing conversation or create and commit a new one.
    If user_id is provided, enforces that an existing conversation matches the user,
    or attaches user_id to a new conversation.
    """
    target_id = session_id or str(uuid.uuid4())
    query = db.query(Conversation).filter(Conversation.id == target_id)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    conv = query.first()

    if not conv:
        now = datetime.now(timezone.utc)
        title = default_title or "New Analysis"
        conv = Conversation(
            id=target_id,
            user_id=user_id,
            title=title,
            created_at=now,
            updated_at=now,
            last_message_at=now,
            parameters_json={},
            analysis_json={},
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def save_chat_turn(
    db: Session,
    session_id: str,
    user_message: str,
    ai_message: str,
    mode: str = "text",
    title: Optional[str] = None,
    parameters: Optional[dict] = None,
    analysis: Optional[dict] = None,
    scenario_comparison: Optional[dict] = None,
    user_id: Optional[str] = None,
) -> Conversation:
    """
    Save user message, assistant message, and update conversation state atomically.
    Ensures the conversation exists and belongs to the user before persisting messages and analysis.
    """
    now = datetime.now(timezone.utc)

    # Step 1: Ensure conversation row exists and is committed in MySQL before persisting messages
    query = db.query(Conversation).filter(Conversation.id == session_id)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    conv = query.first()

    if not conv:
        fallback_title = title or (user_message.strip()[:40] + ("..." if len(user_message.strip()) > 40 else ""))
        conv = Conversation(
            id=session_id,
            user_id=user_id,
            title=fallback_title,
            created_at=now,
            updated_at=now,
            last_message_at=now,
            parameters_json=parameters or {},
            analysis_json=analysis or {},
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    else:
        # Existing conversation: update metadata & snapshots
        if title:
            conv.title = title
        if parameters is not None:
            conv.parameters_json = parameters
        if analysis is not None:
            conv.analysis_json = analysis
        conv.updated_at = now
        conv.last_message_at = now
        try:
            db.commit()
            db.refresh(conv)
        except StaleDataError as sde:
            logger.warning(f"StaleDataError updating conversation {session_id} ({sde}). Re-creating row...")
            db.rollback()
            conv = Conversation(
                id=session_id,
                user_id=user_id,
                title=title or (user_message.strip()[:40] + ("..." if len(user_message.strip()) > 40 else "")),
                created_at=now,
                updated_at=now,
                last_message_at=now,
                parameters_json=parameters or {},
                analysis_json=analysis or {},
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

    # Step 2: Persist user and assistant messages linked to the committed conversation
    ai_time = now + timedelta(seconds=1)
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=user_message,
        message_type="text",
        created_at=now,
    )
    db.add(user_msg)

    ai_metadata = {
        "mode": mode,
        "analysis": analysis,
        "scenarioComparison": scenario_comparison,
        "parameters": parameters,
    }
    ai_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="assistant",
        content=ai_message,
        message_type=mode,
        metadata_json=ai_metadata,
        created_at=ai_time,
    )
    db.add(ai_msg)

    conv.last_message_at = ai_time
    db.commit()
    db.refresh(conv)
    return conv


def get_conversation_list(
    db: Session,
    search_query: Optional[str] = None,
    user_id: Optional[str] = None,
) -> list:
    """List conversations for a specific user, sorted by latest message first."""
    query = db.query(Conversation)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(Conversation.title.like(pattern))
    conversations = query.order_by(Conversation.last_message_at.desc(), Conversation.updated_at.desc()).all()
    return [c.to_summary_dict() for c in conversations]


def get_conversation_detail(
    db: Session,
    session_id: str,
    user_id: Optional[str] = None,
) -> Optional[dict]:
    """Retrieve full conversation details with parsed messages for a specific user."""
    query = db.query(Conversation).filter(Conversation.id == session_id)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    conv = query.first()
    if not conv:
        return None
    return conv.to_detail_dict()


def delete_conversation(
    db: Session,
    session_id: str,
    user_id: Optional[str] = None,
) -> bool:
    """Delete a conversation and all its messages (cascade) for a specific user."""
    query = db.query(Conversation).filter(Conversation.id == session_id)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    conv = query.first()
    if not conv:
        return False
    db.delete(conv)
    db.commit()
    return True
