from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    system: Optional[str] = None  # field for custom system prompt
    query: str = Field(..., min_length=1, description="The search query string")
    k: int = Field(10, gt=0, description="Number of results to return")
    alpha: float = Field(
        0.5, ge=0.0, le=1.0, description="Weight between FAISS and BM25"
    )
    filters: Optional[Dict[str, Union[str, List[str]]]] = (
        None  # e.g., {"category": ["ABF", "confluence"]}
    )
