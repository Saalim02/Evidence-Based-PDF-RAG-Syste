from pydantic import BaseModel
from typing import List, Optional

from app.models.evaluation_models import (
    EvaluationDecision,
    EvaluationResult,
    FeedbackCategory,
)


class QueryRequest(BaseModel):
    question: str
    access_password: Optional[str] = ""
    user_openai_api_key: Optional[str] = ""


class RetrievedChunk(BaseModel):
    chunk_id: int
    file_name: str
    page_number: int
    text: str
    score: float


class HumanReviewRequest(BaseModel):
    decision: EvaluationDecision
    feedback_category: Optional[FeedbackCategory] = None
    feedback_text: Optional[str] = None
    corrected_answer: Optional[str] = None


class QueryResponse(BaseModel):
    status: str
    active_document: Optional[str]
    question: str
    answer: Optional[str]
    confidence: Optional[str]
    best_score: Optional[float]
    average_score: Optional[float]
    evidence: list
    retrieved_chunks: List[RetrievedChunk]
    evaluation: Optional[EvaluationResult] = None
    message: str