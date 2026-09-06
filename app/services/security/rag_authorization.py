import os
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.auth_models import User


def require_authenticated_user(user: User | None) -> User:
    """
    Ensure the request contains a valid authenticated user.
    """
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive.",
        )

    return user


def resolve_authorized_api_key(
    *,
    user: User,
    access_password: str = "",
    user_openai_api_key: str = "",
) -> str:
    """
    Resolve an OpenAI API key after JWT authentication.

    Authorization requires either:
      1. the configured project access password, or
      2. a user-provided OpenAI API key.

    User-provided API keys are used only for the current request.
    They are never persisted here.
    """

    require_authenticated_user(user)

    configured_password = os.getenv("RAG_ACCESS_PASSWORD")

    if not configured_password:
        raise HTTPException(
            status_code=500,
            detail="RAG access password is not configured.",
        )

    supplied_password = str(access_password or "")

    if secrets.compare_digest(
        supplied_password,
        configured_password,
    ):
        backend_key = os.getenv("OPENAI_API_KEY")

        if not backend_key:
            raise HTTPException(
                status_code=500,
                detail="Backend OpenAI API key not configured.",
            )

        return backend_key.strip()

    supplied_key = str(user_openai_api_key or "").strip()

    if not supplied_key:
        raise HTTPException(
            status_code=403,
            detail=(
                "Project authorization required. "
                "Provide the project access password "
                "or your own OpenAI API key."
            ),
        )

    if len(supplied_key) < 20:
        raise HTTPException(
            status_code=400,
            detail="Invalid OpenAI API key.",
        )

    return supplied_key
