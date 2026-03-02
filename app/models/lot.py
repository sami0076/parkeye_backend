from uuid import uuid4

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.database import Base


class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    permit_types: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    is_deck: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    floors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="open"
    )  # "open" | "limited" | "closed"
    status_until: Mapped["datetime | None"] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

