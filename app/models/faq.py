from pydantic import BaseModel, field_validator
from typing import Optional, Union, List, Any
import json


class FAQ(BaseModel):
    id: str
    question: str
    answer: str
    embedding: Optional[List[float]] = None

    @field_validator("embedding", mode="before")
    @classmethod
    def parse_embedding(cls, v: Any) -> Optional[List[float]]:
        if v is None:
            return None
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return []


class FAQCreate(BaseModel):
    question: str
    answer: str


class FAQUpdate(BaseModel):
    question: str
    answer: str


class FAQResponse(BaseModel):
    id: str
    question: str
    answer: str
