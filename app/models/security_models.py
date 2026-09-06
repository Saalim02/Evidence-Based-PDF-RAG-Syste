from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class SecurityDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"


class SecurityCheckResult(BaseModel):
    decision: SecurityDecision
    is_safe: bool
    reasons: List[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=1.0)
