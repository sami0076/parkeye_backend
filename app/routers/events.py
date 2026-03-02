from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.event import EventListResponse, EventSummary
from app.services.events import get_upcoming_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(db: AsyncSession = Depends(get_db)):
    """Upcoming campus events for the next 7 days."""
    events = await get_upcoming_events(db)
    return EventListResponse(
        events=[EventSummary.model_validate(e) for e in events],
    )
