from pydantic import BaseModel
from typing import List, Optional


class SuggestedQuestionsResponse(BaseModel):
    status: str
    active_document: Optional[str] = None
    suggested_questions: List[str]
    message: str