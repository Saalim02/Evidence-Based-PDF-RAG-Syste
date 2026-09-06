import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.models.auth_models import PasswordResetToken, User


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()

# Used when a login email does not exist.
# This helps reduce obvious timing differences between
# existing and non-existing accounts.
DUMMY_PASSWORD_HASH = password_hash.hash(
    "dummy-password-for-timing-protection"
)


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def validate_password(password: str) -> None:
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")

    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )

    if len(password) > 128:
        raise ValueError(
            "Password must not exceed 128 characters."
        )


def hash_password(password: str) -> str:
    validate_password(password)
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "").strip()

    if len(secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be at least 32 characters long."
        )

    return secret

def create_access_token(
    user_id: int,
    token_version: int = 0,
) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": expires_at,
        "token_version": int(token_version),
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> tuple[int, int]:
    payload = jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[JWT_ALGORITHM],
    )

    if payload.get("type") != "access":
        raise ValueError("Invalid token type.")

    subject = payload.get("sub")

    if not subject:
        raise ValueError("Token subject is missing.")

    token_version = payload.get("token_version")

    if token_version is None:
        raise ValueError("Token version is missing.")

    try:
        user_id = int(subject)
        token_version = int(token_version)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid token claims.") from exc

    if user_id <= 0 or token_version < 0:
        raise ValueError("Invalid token claims.")

    return user_id, token_version


def create_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    normalized_email = normalize_email(email)

    if not normalized_email:
        raise ValueError("Email is required.")

    validate_password(password)

    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_user:
        raise ValueError(
            "An account with this email already exists."
        )

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        auth_provider="local",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    normalized_email = normalize_email(email)

    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if user is None:
        # Perform the same expensive password operation
        # even when the account does not exist.
        password_hash.verify(
            password,
            DUMMY_PASSWORD_HASH,
        )
        return None

    if not user.is_active:
        return None

    if not user.password_hash:
        # Google-only account.
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


def create_password_reset_token(
    db: Session,
    user: User,
    expires_minutes: int = 30,
) -> str:
    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=expires_minutes)
    )

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(reset_token)
    db.commit()

    return raw_token


def consume_password_reset_token(
    db: Session,
    raw_token: str,
) -> User | None:
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    reset_token = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash
        )
        .first()
    )

    if reset_token is None:
        return None

    now = datetime.now(timezone.utc)

    if reset_token.used_at is not None:
        return None

    # SQLite does not preserve timezone information for DateTime
    # columns. Normalize the value returned by SQLAlchemy to UTC
    # before performing the expiration comparison.
    expires_at = reset_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = expires_at.astimezone(timezone.utc)

    if expires_at <= now:
        return None

    user = (
        db.query(User)
        .filter(User.id == reset_token.user_id)
        .first()
    )

    if user is None or not user.is_active:
        return None

    reset_token.used_at = now

    db.commit()

    return user


def get_or_create_google_user(
    db: Session,
    email: str,
    google_sub: str,
) -> User:
    normalized_email = normalize_email(email)
    google_sub = str(google_sub or "").strip()

    if not normalized_email:
        raise ValueError("Google account email is missing.")

    if not google_sub:
        raise ValueError("Google account identifier is missing.")

    # First preference: the immutable Google subject identifier.
    user = (
        db.query(User)
        .filter(User.google_sub == google_sub)
        .first()
    )

    if user:
        if not user.is_active:
            raise ValueError("User account is inactive.")

        return user

    # Never silently link Google to an existing local-password account.
    existing_email_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_email_user:
        if existing_email_user.auth_provider == "google":
            existing_email_user.google_sub = google_sub
            db.commit()
            db.refresh(existing_email_user)
            return existing_email_user

        raise ValueError(
            "An account with this email already exists. "
            "Sign in with your password first."
        )

    user = User(
        email=normalized_email,
        password_hash=None,
        auth_provider="google",
        google_sub=google_sub,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user
