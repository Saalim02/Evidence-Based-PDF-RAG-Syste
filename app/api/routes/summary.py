from fastapi import APIRouter, HTTPException
import os

from app.models.query_models import QueryRequest
from app.models.summary_models import SummaryResponse

from app.services.summary_service import (
    generate_pdf_summary
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

        backend_key = os.getenv(
            "OPENAI_API_KEY"
        )

        if not backend_key:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Backend OpenAI API key "
                    "not configured."
                )
            )

        return backend_key

    # -----------------------------------
    # USER API KEY MODE
    # -----------------------------------
    if (
        not user_openai_api_key
        or len(user_openai_api_key.strip()) < 20
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Provide valid access password "
                "or your own OpenAI API key."
            )
        )

    return user_openai_api_key.strip()


# -----------------------------------
# SUMMARY ROUTE
# -----------------------------------
@router.post(
    "/summary",
    response_model=SummaryResponse
)
def get_pdf_summary(
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
    # GENERATE SUMMARY
    # -----------------------------------
    return generate_pdf_summary(
        api_key
    )