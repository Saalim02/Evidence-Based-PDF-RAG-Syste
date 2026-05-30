from pydantic import BaseModel
from typing import List, Optional


class SummaryResponse(BaseModel):
    status: str
    active_document: Optional[str]
    summary: str
    key_topics: List[str]
    message: str