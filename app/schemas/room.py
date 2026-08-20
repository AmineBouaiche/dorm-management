from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import RoomType
from app.schemas.building import BuildingRead


class RoomCreate(BaseModel):
    building_id: int = Field(gt=0)
    room_number: str = Field(min_length=1, max_length=20)
    room_type: RoomType
    capacity: int = Field(gt=0)
    weekly_rate: Decimal = Field(ge=0, max_digits=10, decimal_places=2)


class RoomUpdate(BaseModel):
    building_id: int | None = Field(default=None, gt=0)
    room_number: str | None = Field(default=None, min_length=1, max_length=20)
    room_type: RoomType | None = None
    capacity: int | None = Field(default=None, gt=0)
    weekly_rate: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    is_active: bool | None = None


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    building_id: int
    room_number: str
    room_type: RoomType
    capacity: int
    weekly_rate: Decimal
    is_active: bool
    building: BuildingRead


class AvailabilityWindow(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_date_range(self) -> "AvailabilityWindow":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self
