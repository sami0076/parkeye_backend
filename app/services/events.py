"""Event queries for lot detail and recommendations."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CampusEvent


async def get_upcoming_events_for_lot(
    lot_id: UUID,
    db: AsyncSession,
    *,
    within_days: int = 7,
) -> list:
    """
    Return upcoming campus events that affect this lot (lot_id in affected_lots)
    and end after now, optionally limited to the next N days.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CampusEvent).where(
            CampusEvent.affected_lots.any(str(lot_id)),
            CampusEvent.end_time >= now,
        ).order_by(CampusEvent.start_time)
    )
    events = result.scalars().all()
    if within_days <= 0:
        return list(events)
    cutoff = now + timedelta(days=within_days)
    return [e for e in events if e.start_time <= cutoff]
