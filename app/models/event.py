from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.database import Base


class CampusEvent(Base):
    __tablename__ = "campus_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped["datetime"] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    end_time: Mapped["datetime"] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    impact_level: Mapped[str] = mapped_column(String, nullable=False)
    affected_lots: Mapped[list[str]] = mapped_column(ARRAY(UUID(as_uuid=False)))

