from typing import Any, Optional

from pydantic import BaseModel, Field


class AiModel(BaseModel):
    ai_model_name: Optional[str]
    model: Optional[Any]
    load_time: float = Field(default=None, ge=0)
