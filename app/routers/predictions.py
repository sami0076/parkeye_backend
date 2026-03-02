from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lot import Lot
from app.schemas.occupancy import PredictionResponse
from app.services.prediction import get_prediction

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{lot_id}", response_model=PredictionResponse)
async def predict_occupancy(
    lot_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    lot_result = await db.execute(select(Lot).where(Lot.id == lot_id))
    if lot_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Lot not found")

    return await get_prediction(lot_id, db)
