"""
Recommendation engine for Parkeye.

Ranks parking lots by predicted occupancy and walking distance to a destination.
Applies a +20% occupancy bump for lots affected by campus events near arrival time.
No ML — pure logic on the occupancy_snapshots table.
"""

import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import CampusEvent
from app.models.lot import Lot
from app.models.occupancy import OccupancySnapshot

AVERAGE_WALK_SPEED_KPH = 4.8
EVENT_BUMP = 0.20
TOP_N = 5


def _occupancy_color(pct: float) -> str:
    if pct < 0.6:
        return "green"
    if pct < 0.85:
        return "yellow"
    return "red"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres between two lat/lon points."""
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _walk_minutes(distance_km: float) -> float:
    return round((distance_km / AVERAGE_WALK_SPEED_KPH) * 60, 1)


async def get_recommendations(
    permit_type: str,
    dest_lat: float,
    dest_lon: float,
    arrival_time: datetime,
    duration_min: int,
    db: AsyncSession,
) -> list[dict]:
    """
    Return the top-5 lots ranked by predicted occupancy for the requested
    arrival time, filtered by permit type, with event bumps applied.
    """
    # 1. Filter lots whose permit_types contain the requested type
    result = await db.execute(
        select(Lot).where(Lot.permit_types.any(permit_type))
    )
    lots = result.scalars().all()

    if not lots:
        return []

    arrival_hour = arrival_time.hour
    arrival_day = arrival_time.weekday()

    # 2. Fetch predicted occupancy at arrival_hour for each lot in one query
    lot_ids = [lot.id for lot in lots]
    snap_result = await db.execute(
        select(OccupancySnapshot).where(
            OccupancySnapshot.lot_id.in_(lot_ids),
            OccupancySnapshot.hour_of_day == arrival_hour,
            OccupancySnapshot.day_of_week == arrival_day,
        )
    )
    snapshots_by_lot: dict[str, OccupancySnapshot] = {
        s.lot_id: s for s in snap_result.scalars().all()
    }

    # 3. Find events overlapping the arrival window
    arrival_utc = arrival_time if arrival_time.tzinfo else arrival_time.replace(
        tzinfo=timezone.utc
    )
    departure_utc = arrival_utc + timedelta(minutes=duration_min)

    event_result = await db.execute(
        select(CampusEvent).where(
            CampusEvent.start_time <= departure_utc,
            CampusEvent.end_time >= arrival_utc,
        )
    )
    events = event_result.scalars().all()

    bumped_lot_ids: set[str] = set()
    for event in events:
        for lid in (event.affected_lots or []):
            bumped_lot_ids.add(str(lid))

    # 4. Score each lot
    scored: list[dict] = []
    for lot in lots:
        snap = snapshots_by_lot.get(lot.id)
        pct = snap.occupancy_pct if snap else 0.5

        if str(lot.id) in bumped_lot_ids:
            pct = min(pct + EVENT_BUMP, 1.0)

        distance_km = _haversine_km(lot.lat, lot.lon, dest_lat, dest_lon)

        scored.append({
            "lot_id": lot.id,
            "lot_name": lot.name,
            "predicted_pct": round(pct, 4),
            "color": _occupancy_color(pct),
            "walk_minutes": _walk_minutes(distance_km),
            "confidence": "Estimated from historical patterns",
        })

    # 5. Sort by predicted occupancy ascending, return top 5
    scored.sort(key=lambda x: x["predicted_pct"])
    return scored[:TOP_N]
