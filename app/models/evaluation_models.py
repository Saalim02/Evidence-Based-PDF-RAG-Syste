from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class EvaluationDecision(str, Enum):
    AUTO_APPROVE = "AUTO_APPROVE"
    REVIEW_RECOMMENDED = "REVIEW_RECOMMENDED"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class FeedbackCategory(str, Enum):
    INCORRECT_RETRIEVAL = "incorrect_retrieval"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    HALLUCINATION = "hallucination"
    INCORRECT_ANSWER = "incorrect_answer"
    POOR_SOURCE = "poor_source"
    CITATION_PROBLEM = "citation_problem"
    OTHER = "other"


class EvidenceReference(BaseModel):
    page_number: int
    snippet: str
    chunk_id: Optional[int] = None
    file_name: Optional[str] = None


class ClaimEvaluation(BaseModel):
    claim: str
    supported: bool
    evidence: List[EvidenceReference] = Field(default_factory=list)
    reason: Optional[str] = None


class EvaluationResult(BaseModel):
    evaluation_id: str

    # Owner of this evaluation. Optional only for legacy
    # evaluation files created before user isolation existed.
    user_id: Optional[int] = None

    question: str
    answer: Optional[str] = None

    retrieval_quality: float = Field(
        ge=0.0,
        le=1.0
    )

    source_relevance: float = Field(
        ge=0.0,
        le=1.0
    )

    grounding: float = Field(
        ge=0.0,
        le=1.0
    )

    answer_correctness: float = Field(
        ge=0.0,
        le=1.0
    )

    citation_quality: float = Field(
        ge=0.0,
        le=1.0
    )

    overall_confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    decision: EvaluationDecision

    reasons: List[str] = Field(
        default_factory=list
    )

    claims: List[ClaimEvaluation] = Field(
        default_factory=list
    )


class HumanReview(BaseModel):
    evaluation_id: str

    decision: EvaluationDecision

    feedback_category: Optional[FeedbackCategory] = None

    feedback_text: Optional[str] = None

    corrected_answer: Optional[str] = None


class EvaluationFeedback(BaseModel):
    evaluation_id: str

    feedback_category: FeedbackCategory

    feedback_text: Optional[str] = None

    corrected_answer: Optional[str] = None
