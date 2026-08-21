from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import RoomType

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.building import Building


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("building_id", "room_number", name="uq_room_building_number"),
        CheckConstraint("capacity > 0", name="ck_room_capacity_positive"),
        CheckConstraint("weekly_rate >= 0", name="ck_room_weekly_rate_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="RESTRICT"))
    room_number: Mapped[str] = mapped_column(String(20))
    room_type: Mapped[RoomType] = mapped_column(Enum(RoomType, name="room_type"))
    capacity: Mapped[int] = mapped_column()
    weekly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    building: Mapped["Building"] = relationship(back_populates="rooms")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="room")
