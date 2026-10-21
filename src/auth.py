"""
Authentication and Authorization Module for BizAdvisor.
Provides:
- Argon2id password hashing and verification
- PyJWT HS256 access token encoding, decoding, and signature validation
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

# -----------------------------------------------------------------------------
# Configuration & Secret Validation
# -----------------------------------------------------------------------------
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
    Validates the JWT_SECRET_KEY string.
    Fails safely at startup if missing, empty, too short (< 32 chars),
    or equal to a known development placeholder.
    Never exposes or logs the secret value in exceptions or error logs.
    """
    if secret is None:
        raise RuntimeError(
            "JWT_SECRET_KEY is missing from environment. "
            "A secure secret of at least 32 characters must be configured in .env."
        )

    cleaned = secret.strip()
    if not cleaned:
        raise RuntimeError(
            "JWT_SECRET_KEY is empty. "
            "A secure secret of at least 32 characters must be configured in .env."
        )

    if cleaned.lower() in {p.lower() for p in INSECURE_SECRET_PLACEHOLDERS}:
        raise RuntimeError(
            "JWT_SECRET_KEY is set to an insecure development placeholder. "
            "Configure a unique, cryptographically random secret in .env."
        )

    if len(cleaned) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY is too short (fewer than 32 characters). "
            "Configure a strong secret of at least 32 characters in .env."
        )

    return cleaned


def get_jwt_secret_key() -> str:
    """Loads and validates JWT_SECRET_KEY from environment."""
    return validate_jwt_secret(os.getenv("JWT_SECRET_KEY"))


JWT_SECRET_KEY = get_jwt_secret_key()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
TOKEN_ISSUER = os.getenv("JWT_ISSUER", "bizadvisor-api")

# Argon2id Hasher with memory=64MB, iterations=2, parallelism=1
hasher = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# -----------------------------------------------------------------------------
# Validation Helpers
# -----------------------------------------------------------------------------
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{3,30}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_username(username: str) -> None:
    if not username or not USERNAME_REGEX.match(username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be 3-30 characters long and contain only letters, numbers, underscores, dashes, or dots.",
        )


def validate_email(email: str) -> None:
    if not email or not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format.",
        )


def validate_password_strength(password: str) -> None:
    if not password or len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long.",
        )
    if not any(c.isupper() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one uppercase letter.",
        )
    if not any(c.islower() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one lowercase letter.",
        )
    if not any(c.isdigit() for c in password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must contain at least one number.",
        )


# -----------------------------------------------------------------------------
# Password Operations
# -----------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hashes a password with Argon2id."""
    return hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash."""
    try:
        return hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False


# -----------------------------------------------------------------------------
# JWT Operations
# -----------------------------------------------------------------------------
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": TOKEN_ISSUER,
    })
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=TOKEN_ISSUER,
            options={"require": ["exp", "iat", "iss", "sub"]},
        )
        return payload
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


# -----------------------------------------------------------------------------
# FastAPI Dependencies
# -----------------------------------------------------------------------------
def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Enforces authentication on protected routes.
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
