from pydantic import BaseModel, Field


class JudgeScore(BaseModel):
    """
    Generic structured result returned by an LLM judge.

    Score must be normalized to the range 0.0 - 1.0.
    """
    score: float = Field(
        ge=0.0,
        le=1.0,
    )
    reason: str


class GroundingJudgeResult(BaseModel):
    """
    Structured result for semantic claim-level grounding.
    """
    supported: bool
    score: float = Field(
        ge=0.0,
        le=1.0,
    )
    reason: str
