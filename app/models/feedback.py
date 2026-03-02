from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    lot_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    accuracy_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped["datetime"] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )

