from fastapi import APIRouter
from app.models.question_suggestion_models import SuggestedQuestionsResponse
from app.services.question_suggestion_service import generate_suggested_questions

router = APIRouter()


@router.get("/suggested-questions", response_model=SuggestedQuestionsResponse)
def get_suggested_questions():
    return generate_suggested_questions()