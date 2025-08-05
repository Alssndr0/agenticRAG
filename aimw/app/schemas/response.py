from pydantic import BaseModel


class RunCheckResponse(BaseModel):
    answer: str
