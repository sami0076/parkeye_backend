from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.recommendations import RecommendationResponse
from app.services.recommendation import get_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationResponse)
async def recommend_lots(
    permit_type: str = Query(..., description="e.g. general, west_campus, faculty"),
    dest_lat: float = Query(..., description="Destination latitude"),
    dest_lon: float = Query(..., description="Destination longitude"),
    arrival_time: datetime = Query(..., description="ISO 8601 arrival time"),
    duration_min: int = Query(60, ge=1, description="Expected parking duration in minutes"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return top-5 lots ranked by predicted availability at the requested
    arrival time, filtered by permit type, with walking distance.
    """
    results = await get_recommendations(
        permit_type=permit_type,
        dest_lat=dest_lat,
        dest_lon=dest_lon,
        arrival_time=arrival_time,
        duration_min=duration_min,
        db=db,
    )
    return RecommendationResponse(recommendations=results)
