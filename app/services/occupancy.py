from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lot import Lot
from app.models.occupancy import OccupancySnapshot


def _occupancy_color(pct: float) -> str:
    if pct < 0.6:
        return "green"
    if pct < 0.85:
        return "yellow"
    return "red"


async def get_current_occupancy(lot_id: UUID, db: AsyncSession) -> dict:
    """
    Return the current occupancy for a lot based on the time-of-day snapshot.
    If the lot has an active admin override (status="closed"), returns 1.0/red.
    """
    now = datetime.now()
    hour = now.hour
    day = now.weekday()  # 0=Monday, 6=Sunday

    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = lot_result.scalar_one_or_none()

    if lot is not None and lot.status == "closed":
        return {"occupancy_pct": 1.0, "color": "red"}

    result = await db.execute(
        select(OccupancySnapshot).where(
            OccupancySnapshot.lot_id == lot_id,
            OccupancySnapshot.hour_of_day == hour,
            OccupancySnapshot.day_of_week == day,
        )
    )
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return {"occupancy_pct": 0.0, "color": "green"}

    return {"occupancy_pct": snapshot.occupancy_pct, "color": snapshot.color}
