from uuid import UUID

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    lot_id: UUID
    lot_name: str
    predicted_pct: float
    color: str
    walk_minutes: float
    confidence: str = "Estimated from historical patterns"


class RecommendationResponse(BaseModel):
    recommendations: list[RecommendationItem]
