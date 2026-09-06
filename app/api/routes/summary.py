from fastapi import APIRouter, Depends

from app.models.auth_models import User
from app.models.query_models import QueryRequest
from app.models.summary_models import SummaryResponse

from app.services.security.auth_dependencies import get_current_user
from app.services.security.rag_authorization import resolve_authorized_api_key
from app.services.summary_service import generate_pdf_summary

router = APIRouter()


@router.post(
    "/summary",
    response_model=SummaryResponse
)
def get_pdf_summary(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    api_key = resolve_authorized_api_key(
        user=current_user,
        access_password=request.access_password,
        user_openai_api_key=request.user_openai_api_key,
    )

    return generate_pdf_summary(
        api_key,
        user_id=current_user.id,
    )
