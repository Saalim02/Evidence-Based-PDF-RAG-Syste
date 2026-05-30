from pydantic import BaseModel
from typing import List, Optional


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
    message: str