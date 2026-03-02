from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventSummary(BaseModel):
    id: UUID
    title: str
    start_time: datetime
    end_time: datetime
    impact_level: str

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    events: list[EventSummary]
