from uuid import UUID

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    lot_id: UUID
    accuracy_rating: int = Field(..., ge=1, le=5)
    experience_rating: int = Field(..., ge=1, le=5)
    note: str | None = None
