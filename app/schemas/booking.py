from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import BookingStatus
from app.schemas.room import RoomRead
from app.schemas.student import StudentRead


class BookingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_id: int = Field(gt=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self) -> "BookingCreate":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if (self.end_date - self.start_date).days > 730:
            raise ValueError("booking period cannot exceed 730 days")
        return self


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: date
    end_date: date
    amount: Decimal
    status: BookingStatus
    created_at: datetime
    student: StudentRead
    room: RoomRead


class RevenueSummary(BaseModel):
    total_confirmed_revenue: Decimal
    confirmed_booking_count: int
