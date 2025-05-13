from typing import Dict

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The question to be answered.")
    documents_json: Dict = Field(
        ..., description="A dictionary representing the documents in JSON format."
    )
