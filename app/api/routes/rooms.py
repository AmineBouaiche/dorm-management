from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.room import AvailabilityWindow, RoomCreate, RoomRead, RoomUpdate
from app.services import room_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
def list_rooms(db: Session = Depends(get_db)) -> list[RoomRead]:
    return room_service.list_rooms(db, active_only=True)


@router.get("/available", response_model=list[RoomRead])
def list_available_rooms(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
) -> list[RoomRead]:
    try:
        window = AvailabilityWindow(start_date=start_date, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be before end_date",
        ) from exc

    return room_service.list_available_rooms(db, window.start_date, window.end_date)


@router.get("/{room_id}", response_model=RoomRead)
def get_room(room_id: Annotated[int, Path(gt=0)], db: Session = Depends(get_db)) -> RoomRead:
    try:
        return room_service.get_room(db, room_id, active_only=True)
    except room_service.RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found") from exc


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    data: RoomCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoomRead:
    try:
        return room_service.create_room(db, data)
    except room_service.BuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found") from exc
    except room_service.InactiveBuildingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Building is inactive") from exc
    except room_service.RoomAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room number already exists in this building",
        ) from exc


@router.patch("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: Annotated[int, Path(gt=0)],
    data: RoomUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoomRead:
    try:
        return room_service.update_room(db, room_id, data)
    except room_service.RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found") from exc
    except room_service.BuildingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found") from exc
    except room_service.InactiveBuildingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Building is inactive") from exc
    except room_service.RoomAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Room number already exists in this building",
        ) from exc
