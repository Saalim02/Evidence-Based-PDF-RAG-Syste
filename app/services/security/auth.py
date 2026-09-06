import os
import secrets

from fastapi import HTTPException


def resolve_api_key(
    access_password: str,
    user_openai_api_key: str,
) -> str:
    """
    Resolve the OpenAI API key using either:
    1. Backend access password -> server-side OPENAI_API_KEY
    2. User-provided OpenAI API key
    """

    configured_password = os.getenv("RAG_ACCESS_PASSWORD")

    if not configured_password:
        raise HTTPException(
            status_code=500,
            detail="RAG access password is not configured.",
        )

    if secrets.compare_digest(
        str(access_password or ""),
        configured_password,
    ): 
        backend_key = os.getenv("OPENAI_API_KEY")

        if not backend_key:
            raise HTTPException(
                status_code=500,
                detail="Backend OpenAI API key not configured.",
            )

        return backend_key.strip()

    if not user_openai_api_key:
        raise HTTPException(
            status_code=400,
            detail=(
                "Provide valid access password "
                "or your own OpenAI API key."
            ),
        )

    user_openai_api_key = user_openai_api_key.strip()

    if len(user_openai_api_key) < 20:
        raise HTTPException(
            status_code=400,
            detail="Invalid OpenAI API key.",
        )

    return user_openai_api_key
