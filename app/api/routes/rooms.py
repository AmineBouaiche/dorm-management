from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.pagination import Pagination, add_pagination_headers, pagination_params
from app.db.database import get_db
from app.models.user import User
from app.schemas.room import AvailabilityWindow, RoomCreate, RoomRead, RoomUpdate
from app.services import audit_service, room_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomRead])
def list_rooms(
    response: Response,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[RoomRead]:
    total = room_service.count_rooms(db, active_only=True)
    add_pagination_headers(response, pagination=pagination, total=total)
    return room_service.list_rooms(
        db, active_only=True, offset=pagination.offset, limit=pagination.per_page
    )


@router.get("/available", response_model=list[RoomRead])
def list_available_rooms(
    response: Response,
    start_date: date = Query(...),
    end_date: date = Query(...),
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[RoomRead]:
    try:
        window = AvailabilityWindow(start_date=start_date, end_date=end_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be before end_date",
        ) from exc

    total = room_service.count_available_rooms(db, window.start_date, window.end_date)
    add_pagination_headers(response, pagination=pagination, total=total)
    return room_service.list_available_rooms(
        db,
        window.start_date,
        window.end_date,
        offset=pagination.offset,
        limit=pagination.per_page,
    )


@router.get("/{room_id}", response_model=RoomRead)
def get_room(room_id: Annotated[int, Path(gt=0)], db: Session = Depends(get_db)) -> RoomRead:
    try:
        return room_service.get_room(db, room_id, active_only=True)
    except room_service.RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found") from exc


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    data: RoomCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoomRead:
    try:
        room = room_service.create_room(db, data)
        audit_service.record_event(
            db,
            actor_user_id=admin.id,
            action="room.create",
            resource_type="room",
            resource_id=room.id,
            request_id=request.state.request_id,
        )
        return room
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
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RoomRead:
    try:
        room = room_service.update_room(db, room_id, data)
        audit_service.record_event(
            db,
            actor_user_id=admin.id,
            action="room.update",
            resource_type="room",
            resource_id=room.id,
            request_id=request.state.request_id,
            details={"changed_fields": sorted(data.model_dump(exclude_unset=True).keys())},
        )
        return room
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
