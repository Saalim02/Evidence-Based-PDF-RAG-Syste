from fastapi import APIRouter, HTTPException
import os

from app.models.query_models import QueryRequest

from app.models.question_suggestion_models import (
    SuggestedQuestionsResponse
)

from app.services.question_suggestion_service import (
    generate_suggested_questions
)

router = APIRouter()


# -----------------------------------
# API KEY RESOLUTION
# -----------------------------------
def resolve_api_key(
    access_password: str,
    user_openai_api_key: str
):

    # -----------------------------------
    # BACKEND ACCESS MODE
    # -----------------------------------
    if access_password == "20022004":

        backend_key = os.getenv("OPENAI_API_KEY")

        if not backend_key:

            raise HTTPException(
                status_code=500,
                detail="Backend OpenAI API key not configured."
            )

        return backend_key

    # -----------------------------------
    # USER API KEY MODE
    # -----------------------------------
    if not user_openai_api_key:

        raise HTTPException(
            status_code=400,
            detail=(
                "Provide valid access password "
                "or your own OpenAI API key."
            )
        )

    return user_openai_api_key


@router.post(
    "/suggested-questions",
    response_model=SuggestedQuestionsResponse
)
def get_suggested_questions(
    request: QueryRequest
):

    # -----------------------------------
    # RESOLVE API KEY
    # -----------------------------------
    api_key = resolve_api_key(
        request.access_password,
        request.user_openai_api_key
    )

    # -----------------------------------
    # GENERATE QUESTIONS
    # -----------------------------------
    return generate_suggested_questions(
        api_key
    )