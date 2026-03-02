from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.occupancy import OccupancySnapshot


def _occupancy_color(pct: float) -> str:
    if pct < 0.6:
        return "green"
    if pct < 0.85:
        return "yellow"
    return "red"


async def _get_snapshot_at(
    lot_id: UUID, hour: int, day: int, db: AsyncSession
) -> dict:
    """Fetch the occupancy snapshot for a specific hour/day, with a safe fallback."""
    result = await db.execute(
        select(OccupancySnapshot).where(
            OccupancySnapshot.lot_id == lot_id,
            OccupancySnapshot.hour_of_day == hour,
            OccupancySnapshot.day_of_week == day,
        )
    )
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        return {"pct": 0.5, "color": "green"}

    return {"pct": snapshot.occupancy_pct, "color": snapshot.color}


async def get_prediction(lot_id: UUID, db: AsyncSession) -> dict:
    """
    Rule-based look-ahead prediction. Returns predicted occupancy at t+1 and
    t+2 hours by reading historical snapshots for those future hours on the
    same day_of_week. No ML model — pure table lookup.
    """
    now = datetime.now()
    day = now.weekday()

    t15_hour = (now.hour + 1) % 24
    t30_hour = (now.hour + 2) % 24

    t15 = await _get_snapshot_at(lot_id, t15_hour, day, db)
    t30 = await _get_snapshot_at(lot_id, t30_hour, day, db)

    return {
        "t15": t15,
        "t30": t30,
        "note": "Estimated from historical patterns",
    }
