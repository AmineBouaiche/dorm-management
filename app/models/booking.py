from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Numeric, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import BookingStatus

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.student import Student


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus, name="booking_status"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("start_date < end_date", name="ck_booking_valid_date_range"),
        CheckConstraint("amount >= 0", name="ck_booking_amount_non_negative"),
        ExcludeConstraint(
            (room_id, "="),
            (func.daterange(start_date, end_date, "[)"), "&&"),
            where=text("status IN ('PENDING', 'CONFIRMED')"),
            using="gist",
            name="excl_booking_room_overlap",
        ),
        ExcludeConstraint(
            (student_id, "="),
            (func.daterange(start_date, end_date, "[)"), "&&"),
            where=text("status IN ('PENDING', 'CONFIRMED')"),
            using="gist",
            name="excl_booking_student_overlap",
        ),
    )

    student: Mapped["Student"] = relationship(back_populates="bookings")
    room: Mapped["Room"] = relationship(back_populates="bookings")
