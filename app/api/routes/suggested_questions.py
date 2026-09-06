from fastapi import APIRouter, Depends

from app.models.auth_models import User
from app.models.query_models import QueryRequest
from app.models.question_suggestion_models import SuggestedQuestionsResponse

from app.services.security.auth_dependencies import get_current_user
from app.services.security.rag_authorization import resolve_authorized_api_key
from app.services.question_suggestion_service import generate_suggested_questions

router = APIRouter()


@router.post(
    "/suggested-questions",
    response_model=SuggestedQuestionsResponse
)
def get_suggested_questions(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):
    api_key = resolve_authorized_api_key(
        user=current_user,
        access_password=request.access_password,
        user_openai_api_key=request.user_openai_api_key,
    )

    return generate_suggested_questions(
        api_key,
        user_id=current_user.id,
    )
