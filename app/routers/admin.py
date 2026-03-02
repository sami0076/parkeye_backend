from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_current_user
from app.database import get_db
from app.models.lot import Lot
from app.schemas.lot import AdminLotStatusUpdate, LotResponse
from app.services.occupancy import get_current_occupancy

router = APIRouter(prefix="/admin", tags=["admin"])


@router.patch("/lots/{lot_id}/status", response_model=LotResponse)
async def update_lot_status(
    lot_id: UUID,
    body: AdminLotStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update lot status (open/limited/closed). Requires admin JWT claim."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    lot = lot_result.scalar_one_or_none()
    if lot is None:
        raise HTTPException(status_code=404, detail="Lot not found")
    lot.status = body.status
    lot.status_until = body.status_until
    lot.status_reason = body.status_reason
    await db.commit()
    await db.refresh(lot)
    occ = await get_current_occupancy(lot_id, db)
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
        occupancy_pct=occ["occupancy_pct"],
        color=occ["color"],
    )
