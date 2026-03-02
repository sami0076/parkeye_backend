from uuid import UUID

from pydantic import BaseModel


class OccupancySnapshot(BaseModel):
    lot_id: UUID
    hour_of_day: int
    day_of_week: int
    occupancy_pct: float
    color: str

    model_config = {"from_attributes": True}


class OccupancyHistoryPoint(BaseModel):
    hour_of_day: int
    day_of_week: int
    occupancy_pct: float
    color: str


class OccupancyHistoryResponse(BaseModel):
    data: list[OccupancyHistoryPoint]


class PredictionPoint(BaseModel):
    pct: float
    color: str


class PredictionResponse(BaseModel):
    t15: PredictionPoint
    t30: PredictionPoint
    note: str = "Estimated from historical patterns"


class OccupancyBroadcastItem(BaseModel):
    """Single item in the WebSocket occupancy broadcast payload."""

    lot_id: str
    occupancy_pct: float
    color: str
