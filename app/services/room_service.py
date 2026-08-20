from datetime import date

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking
from app.models.building import Building
from app.models.enums import BookingStatus
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate


class RoomNotFoundError(Exception):
    pass


class BuildingNotFoundError(Exception):
    pass


class InactiveBuildingError(Exception):
    pass


class RoomAlreadyExistsError(Exception):
    pass


def list_rooms(db: Session, *, active_only: bool = True) -> list[Room]:
    statement = select(Room).join(Room.building).options(joinedload(Room.building))
    if active_only:
        statement = statement.where(Room.is_active.is_(True), Building.is_active.is_(True))
    statement = statement.order_by(Room.building_id, Room.room_number)
    return list(db.scalars(statement).all())


def get_room(db: Session, room_id: int, *, active_only: bool = True) -> Room:
    statement = (
        select(Room)
        .join(Room.building)
        .options(joinedload(Room.building))
        .where(Room.id == room_id)
    )
    if active_only:
        statement = statement.where(Room.is_active.is_(True), Building.is_active.is_(True))
    room = db.scalar(statement)
    if room is None:
        raise RoomNotFoundError
    return room


def _get_target_building(db: Session, building_id: int) -> Building:
    building = db.get(Building, building_id)
    if building is None:
        raise BuildingNotFoundError
    if not building.is_active:
        raise InactiveBuildingError
    return building


def create_room(db: Session, data: RoomCreate) -> Room:
    _get_target_building(db, data.building_id)

    room = Room(
        building_id=data.building_id,
        room_number=data.room_number.strip(),
        room_type=data.room_type,
        capacity=data.capacity,
        weekly_rate=data.weekly_rate,
        is_active=True,
    )
    db.add(room)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise RoomAlreadyExistsError from exc

    return get_room(db, room.id, active_only=False)


def update_room(db: Session, room_id: int, data: RoomUpdate) -> Room:
    room = get_room(db, room_id, active_only=False)
    changes = data.model_dump(exclude_unset=True)

    if "building_id" in changes:
        _get_target_building(db, changes["building_id"])
    if "room_number" in changes:
        changes["room_number"] = changes["room_number"].strip()

    for field, value in changes.items():
        setattr(room, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise RoomAlreadyExistsError from exc

    return get_room(db, room.id, active_only=False)


def list_available_rooms(db: Session, start_date: date, end_date: date) -> list[Room]:
    blocking_booking_exists = exists(
        select(Booking.id).where(
            Booking.room_id == Room.id,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
            Booking.start_date < end_date,
            Booking.end_date > start_date,
        )
    )

    statement = (
        select(Room)
        .join(Room.building)
        .options(joinedload(Room.building))
        .where(
            Room.is_active.is_(True),
            Building.is_active.is_(True),
            ~blocking_booking_exists,
        )
        .order_by(Room.building_id, Room.room_number)
    )
    return list(db.scalars(statement).all())
