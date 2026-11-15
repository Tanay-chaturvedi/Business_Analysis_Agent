"""
src/auth.py - Authentication and Authorization Module for BizAdvisor

Provides:
- Argon2id password hashing and verification
- PyJWT HS256 access token encoding, decoding, and signature validation
- Input validation for credentials (username, email, password strength)
- FastAPI dependencies for authenticated routes and user resolution
"""

import os
import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from src.database import get_db, User

load_dotenv()

logger = logging.getLogger("bizadvisor.auth")


# Configuration & Secret Validation
INSECURE_SECRET_PLACEHOLDERS = {
    "bizadvisor-dev-fallback-secret-key-32-chars-minimum",
    "your_jwt_secret_key_minimum_32_characters_here",
    "your_jwt_secret_key_here",
    "change_me",
    "secret",
    "secretkey",
    "changethis",
    "placeholder",
    "changeme",
}


def validate_jwt_secret(secret: Optional[str]) -> str:
    """
    Validate that JWT_SECRET_KEY is present, not empty, at least 32 characters,
    and not set to a known development placeholder.
    """
    if secret is None:
        raise RuntimeError("JWT_SECRET_KEY is missing from environment. A secure secret is required.")

    cleaned = secret.strip()
    if not cleaned:
        raise RuntimeError("JWT_SECRET_KEY is empty. A secure secret of at least 32 characters is required.")

    if cleaned.lower() in {p.lower() for p in INSECURE_SECRET_PLACEHOLDERS}:
        raise RuntimeError("JWT_SECRET_KEY is set to an insecure development placeholder.")

    if len(cleaned) < 32:
        raise RuntimeError("JWT_SECRET_KEY is too short (fewer than 32 characters).")

    return cleaned


def get_jwt_secret_key() -> str:
    """Load and validate JWT_SECRET_KEY from environment."""
    return validate_jwt_secret(os.getenv("JWT_SECRET_KEY"))


JWT_SECRET_KEY = get_jwt_secret_key()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
TOKEN_ISSUER = os.getenv("JWT_ISSUER", "bizadvisor-api")

# Argon2id Hasher (64MB memory, 2 iterations, 1 lane)
hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# Input Validation Helpers
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$")


def validate_username(username: str) -> None:
    """Validate username length (3-30) and allowed characters."""
    if not username or not USERNAME_PATTERN.fullmatch(username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be 3-30 characters long and contain only letters, numbers, underscores, dashes, or dots.",
        )


def validate_email(email: str) -> None:
    """Validate email address format."""
    if not email or not EMAIL_PATTERN.fullmatch(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format.",
        )


def validate_password_strength(password: str) -> None:
    """Validate password complexity (>= 8 chars, uppercase, lowercase, digit)."""
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long.",
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter.",
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter.",
        )
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number.",
        )

# Password Operations
def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash."""
    try:
        return hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception:
        logger.exception("Password verification failed unexpectedly.")
        return False

# JWT Operations
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token with standard claims (exp, iat, iss, sub)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {**data, "exp": expire, "iat": now, "iss": TOKEN_ISSUER}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token, enforcing signature and claims."""
    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=TOKEN_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# FastAPI Dependencies
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Enforce authentication on protected routes.
    Resolves the authenticated user from the JWT bearer token.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
