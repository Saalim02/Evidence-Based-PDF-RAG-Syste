from fastapi import APIRouter
from app.models.summary_models import SummaryResponse
from app.services.summary_service import generate_pdf_summary

router = APIRouter()


@router.get("/summary", response_model=SummaryResponse)
def get_pdf_summary():
    return generate_pdf_summary()