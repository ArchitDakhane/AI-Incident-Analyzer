"""Authentication service with JWT and password hashing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationException, ConflictException, ValidationException
from app.models.user import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True when the plain text password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password securely."""
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""
    expires = datetime.now(timezone.utc) + (
        expires_delta or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expires, "token_type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a signed refresh token."""
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {"sub": subject, "exp": expires, "token_type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
    except JWTError as exc:  # pragma: no cover - exercised in runtime
        raise AuthenticationException("Invalid or expired token") from exc

    return payload


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate a user with the supplied credentials."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise AuthenticationException("Incorrect email or password")
    if not user.is_active:
        raise AuthenticationException("User account is disabled")

    return user


def register_user(db: Session, *, email: str, username: str, password: str, full_name: str | None) -> User:
    """Register a new user account."""
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)).first()
    if existing_user:
        raise ConflictException(
            "A user with that email or username already exists")

    user = User(
        email=email,
        username=username,
        password_hash=get_password_hash(password),
        full_name=full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(db: Session, token: str) -> User:
    """Resolve the currently authenticated user from a token."""
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise AuthenticationException("User not found or inactive")

    return user


def validate_refresh_token(db: Session, refresh_token: str) -> User:
    """Validate a refresh token."""
    payload = decode_token(refresh_token)
    if payload.get("token_type") != "refresh":
        raise ValidationException("Invalid token type")

    return get_current_user(db, refresh_token)
