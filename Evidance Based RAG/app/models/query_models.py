from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    question: str


class RetrievedChunk(BaseModel):
    chunk_id: int
    file_name: str
    page_number: int
    text: str
    score: float


class EvidenceItem(BaseModel):
    page_number: int
    snippet: str
    image_path: str


class QueryResponse(BaseModel):
    status: str
    active_document: Optional[str]
    question: Optional[str] = None
    answer: Optional[str] = None
    confidence: Optional[str] = None
    best_score: Optional[float] = None
    average_score: Optional[float] = None
    evidence: List[EvidenceItem] = []
    retrieved_chunks: List[RetrievedChunk]
    message: str