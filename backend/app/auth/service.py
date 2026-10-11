"""Authentication service with JWT and password hashing."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationException, ConflictException
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.dashboard import invalidate_dashboard_cache

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


def _refresh_token_hash(token_id: str) -> str:
    return hashlib.sha256(token_id.encode("utf-8")).hexdigest()


def create_refresh_token(
    db: Session,
    subject: str,
    *,
    expires_delta: timedelta = timedelta(days=7),
    commit: bool = True,
) -> str:
    """Create a refresh token and persist only its hashed identifier."""
    issued_at = datetime.now(timezone.utc)
    expires = issued_at + expires_delta
    token_id = secrets.token_urlsafe(32)
    payload = {
        "sub": subject,
        "exp": expires,
        "iat": issued_at,
        "jti": token_id,
        "token_type": "refresh",
    }
    db.add(
        RefreshToken(
            token_hash=_refresh_token_hash(token_id),
            user_id=int(subject),
            expires_at=expires,
        )
    )
    if commit:
        db.commit()
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


def register_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    full_name: str | None,
) -> User:
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
    invalidate_dashboard_cache()
    return user


def get_current_user(db: Session, token: str) -> User:
    """Resolve the currently authenticated user from a token."""
    payload = decode_token(token)
    if payload.get("token_type") != "access":
        raise AuthenticationException("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("Invalid token payload")

    try:
        user = db.query(User).filter(User.id == int(user_id)).first()
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("Invalid token payload") from exc
    if not user or not user.is_active:
        raise AuthenticationException("User not found or inactive")

    return user


def rotate_refresh_token(db: Session, refresh_token: str) -> tuple[User, str, str]:
    """Atomically consume a refresh token and issue its replacement pair."""
    payload = decode_token(refresh_token)
    if payload.get("token_type") != "refresh":
        raise AuthenticationException("Invalid token type")

    user_id = payload.get("sub")
    token_id = payload.get("jti")
    if not user_id or not isinstance(token_id, str):
        raise AuthenticationException("Invalid token payload")
    try:
        numeric_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("Invalid token payload") from exc

    now = datetime.now(timezone.utc)
    consumed = db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == _refresh_token_hash(token_id),
            RefreshToken.user_id == numeric_user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
        .returning(RefreshToken.expires_at)
    ).first()
    if consumed is None:
        db.rollback()
        raise AuthenticationException(
            "Refresh token has already been used or revoked")

    expires_at = consumed.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        db.commit()
        raise AuthenticationException("Refresh token has expired")

    user = db.query(User).filter(User.id == numeric_user_id).first()
    if not user or not user.is_active:
        db.rollback()
        raise AuthenticationException("User not found or inactive")

    access_token = create_access_token(str(user.id))
    new_refresh_token = create_refresh_token(db, str(user.id), commit=False)
    db.commit()
    return user, access_token, new_refresh_token


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    """Revoke a refresh token; repeated logout calls are harmless."""
    payload = decode_token(refresh_token)
    token_id = payload.get("jti")
    user_id = payload.get("sub")
    if payload.get("token_type") != "refresh" or not isinstance(token_id, str) or not user_id:
        raise AuthenticationException("Invalid refresh token")
    try:
        numeric_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise AuthenticationException("Invalid refresh token") from exc

    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == _refresh_token_hash(token_id),
            RefreshToken.user_id == numeric_user_id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.commit()
