from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class QuestionDTO(BaseModel):
    id: int
    question: str
    options: List[str]
    option_images: Optional[List[str]] = None
    irt_a: Optional[float] = None
    irt_b: Optional[float] = None
    image: Optional[str] = None
    lang: Optional[str] = None


class AttemptStartResponse(BaseModel):
    attempt_id: str
    set_id: str


class AttemptQuestionsResponse(BaseModel):
    attempt_id: str
    set_id: str
    items: List[QuestionDTO]
