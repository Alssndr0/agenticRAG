from pydantic import BaseModel


class RunCheckRequest(BaseModel):
    document_path: str
    query: str
