import random
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


async def get_lots_with_current_occupancy(db: AsyncSession) -> list[dict]:
    """
    Return all lots with their current occupancy_pct and color.
    Admin override (status=closed) is applied per lot.
    """
    result = await db.execute(select(Lot))
    lots = result.scalars().all()
    out = []
    for lot in lots:
        occ = await get_current_occupancy(UUID(lot.id), db)
        out.append({
            "lot": lot,
            "occupancy_pct": occ["occupancy_pct"],
            "color": occ["color"],
        })
    return out


async def get_occupancy_history(lot_id: UUID, db: AsyncSession) -> list[dict]:
    """
    Return hourly occupancy for the lot across all 24 hours x 7 days.
    Used for the past-7-days graph on the lot detail screen.
    """
    result = await db.execute(
        select(OccupancySnapshot).where(
            OccupancySnapshot.lot_id == lot_id,
        ).order_by(
            OccupancySnapshot.day_of_week,
            OccupancySnapshot.hour_of_day,
        )
    )
    snapshots = result.scalars().all()
    return [
        {
            "hour_of_day": s.hour_of_day,
            "day_of_week": s.day_of_week,
            "occupancy_pct": s.occupancy_pct,
            "color": s.color,
        }
        for s in snapshots
    ]


async def get_floor_occupancy(lot_id: UUID, db: AsyncSession) -> list[dict] | None:
    """
    Per-floor occupancy for parking decks only. Synthetic breakdown from
    current lot occupancy (no per-floor data in DB for MVP).
    Returns None if lot is not a deck.
    """
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = lot_result.scalar_one_or_none()
    if lot is None or not lot.is_deck or lot.floors is None or lot.floors < 1:
        return None
    occ = await get_current_occupancy(lot_id, db)
    base_pct = occ["occupancy_pct"]
    random.seed(hash(str(lot_id)) % (2**32))
    floors_list = []
    for floor in range(1, lot.floors + 1):
        variance = random.uniform(0.85, 1.15)
        pct = min(1.0, max(0.0, base_pct * variance))
        color = _occupancy_color(pct)
        floors_list.append({"floor_number": floor, "occupancy_pct": pct, "color": color})
    return floors_list
