from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    lot_id: UUID
    accuracy_rating: int = Field(..., ge=1, le=5)
    experience_rating: int = Field(..., ge=1, le=5)
    note: str | None = None


class FeedbackResponse(BaseModel):
    id: UUID
    lot_id: UUID
    created_at: datetime
