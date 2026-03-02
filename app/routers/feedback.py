from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import User, get_optional_user
from app.database import get_db
from app.models.feedback import Feedback
from app.models.lot import Lot
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    body: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """Submit parking accuracy / experience feedback for a lot."""
    lot_result = await db.execute(select(Lot).where(Lot.id == str(body.lot_id)))
    if lot_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Lot not found")

    now = datetime.now(timezone.utc)
    feedback = Feedback(
        id=str(uuid4()),
        user_id=str(current_user.id) if current_user else None,
        lot_id=str(body.lot_id),
        accuracy_rating=body.accuracy_rating,
        experience_rating=body.experience_rating,
        note=body.note,
        created_at=now,
    )
    db.add(feedback)
    await db.commit()

    return FeedbackResponse(
        id=UUID(feedback.id),
        lot_id=UUID(feedback.lot_id),
        created_at=now,
    )
