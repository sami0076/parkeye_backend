from sqlalchemy import Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OccupancySnapshot(Base):
    __tablename__ = "occupancy_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    occupancy_pct: Mapped[float] = mapped_column(Float, nullable=False)
    color: Mapped[str] = mapped_column(nullable=False)

