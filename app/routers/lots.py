from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lot import Lot
from app.schemas.event import EventSummary
from app.schemas.lot import (
    FloorsResponse,
    LotDetailResponse,
    LotListResponse,
    LotResponse,
)
from app.schemas.occupancy import OccupancyHistoryResponse
from app.services.events import get_upcoming_events_for_lot
from app.services.occupancy import (
    get_current_occupancy,
    get_floor_occupancy,
    get_lots_with_current_occupancy,
    get_occupancy_history,
)

router = APIRouter(prefix="/lots", tags=["lots"])


def _lot_to_response(lot: Lot, occupancy_pct: float, color: str) -> LotResponse:
    return LotResponse(
        id=lot.id,
        name=lot.name,
        capacity=lot.capacity,
        permit_types=lot.permit_types or [],
        lat=lot.lat,
        lon=lot.lon,
        is_deck=lot.is_deck,
        floors=lot.floors,
        status=lot.status,
        status_until=lot.status_until,
        status_reason=lot.status_reason,
        occupancy_pct=occupancy_pct,
        color=color,
    )


@router.get("", response_model=LotListResponse)
async def list_lots(db: AsyncSession = Depends(get_db)):
    """All lots with current occupancy_pct, color, and admin status (for iOS map)."""
    rows = await get_lots_with_current_occupancy(db)
    lots = [
        _lot_to_response(row["lot"], row["occupancy_pct"], row["color"])
        for row in rows
    ]
    return LotListResponse(lots=lots)


@router.get("/{lot_id}", response_model=LotDetailResponse)
async def get_lot(
    lot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Single lot with occupancy, permit types, status, and upcoming events."""
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = lot_result.scalar_one_or_none()
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    occ = await get_current_occupancy(lot_id, db)
    events = await get_upcoming_events_for_lot(lot_id, db)
    return LotDetailResponse(
        id=lot.id,
        name=lot.name,
        capacity=lot.capacity,
        permit_types=lot.permit_types or [],
        lat=lot.lat,
        lon=lot.lon,
        is_deck=lot.is_deck,
        floors=lot.floors,
        status=lot.status,
        status_until=lot.status_until,
        status_reason=lot.status_reason,
        occupancy_pct=occ["occupancy_pct"],
        color=occ["color"],
        upcoming_events=[EventSummary.model_validate(e) for e in events],
    )


@router.get("/{lot_id}/history", response_model=OccupancyHistoryResponse)
async def get_lot_history(
    lot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Hourly occupancy for past 7 days (for detail screen graph)."""
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    if lot_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    data = await get_occupancy_history(lot_id, db)
    return OccupancyHistoryResponse(data=data)


@router.get("/{lot_id}/floors", response_model=FloorsResponse)
async def get_lot_floors(
    lot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Per-floor occupancy breakdown (parking decks only)."""
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = lot_result.scalar_one_or_none()
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    floors = await get_floor_occupancy(lot_id, db)
    if floors is None:
        raise HTTPException(
            status_code=404,
            detail="Lot is not a parking deck or has no floor data",
        )
    return FloorsResponse(floors=floors)
