from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LotResponse(BaseModel):
    id: UUID
    name: str
    capacity: int
    permit_types: list[str]
    lat: float
    lon: float
    is_deck: bool
    floors: int | None = None
    status: str
    status_until: datetime | None = None
    status_reason: str | None = None
    occupancy_pct: float
    color: str

    model_config = {"from_attributes": True}


class LotListResponse(BaseModel):
    lots: list[LotResponse]
