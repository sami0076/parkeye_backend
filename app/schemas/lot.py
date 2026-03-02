from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.schemas.event import EventSummary


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


class LotDetailResponse(BaseModel):
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
    upcoming_events: list[EventSummary] = []

    model_config = {"from_attributes": True}


class AdminLotStatusUpdate(BaseModel):
    status: Literal["open", "limited", "closed"]
    status_until: datetime | None = None
    status_reason: str | None = None


class FloorOccupancy(BaseModel):
    floor_number: int
    occupancy_pct: float
    color: str


class FloorsResponse(BaseModel):
    floors: list[FloorOccupancy]
