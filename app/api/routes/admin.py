from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.core.pagination import Pagination, add_pagination_headers, pagination_params
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin import AdminAnalytics
from app.schemas.audit import AuditLogRead
from app.schemas.building import BuildingRead
from app.schemas.room import RoomRead
from app.schemas.booking import BookingRead
from app.schemas.student import StudentRead
from app.services import audit_service, booking_service, building_service, room_service, student_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def _student_to_read(student) -> StudentRead:
    return StudentRead(
        id=student.id,
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.user.email,
    )


@router.get("/buildings", response_model=list[BuildingRead])
def list_all_buildings(
    response: Response,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[BuildingRead]:
    total = building_service.count_buildings(db, active_only=False)
    add_pagination_headers(response, pagination=pagination, total=total)
    return building_service.list_buildings(
        db, active_only=False, offset=pagination.offset, limit=pagination.per_page
    )


@router.get("/rooms", response_model=list[RoomRead])
def list_all_rooms(
    response: Response,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[RoomRead]:
    total = room_service.count_rooms(db, active_only=False)
    add_pagination_headers(response, pagination=pagination, total=total)
    return room_service.list_rooms(
        db, active_only=False, offset=pagination.offset, limit=pagination.per_page
    )


@router.get("/students", response_model=list[StudentRead])
def list_students(
    response: Response,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[StudentRead]:
    total = student_service.count_students(db)
    add_pagination_headers(response, pagination=pagination, total=total)
    students = student_service.list_students(
        db, offset=pagination.offset, limit=pagination.per_page
    )
    return [_student_to_read(student) for student in students]


@router.get("/bookings", response_model=list[BookingRead])
def list_bookings(
    response: Response,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[BookingRead]:
    total = booking_service.count_bookings(db)
    add_pagination_headers(response, pagination=pagination, total=total)
    return booking_service.list_bookings(
        db, offset=pagination.offset, limit=pagination.per_page
    )


@router.patch("/bookings/{booking_id}/confirm", response_model=BookingRead)
def confirm_booking(
    booking_id: Annotated[int, Path(gt=0)],
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BookingRead:
    try:
        booking = booking_service.confirm_booking(db, booking_id)
        audit_service.record_event(
            db,
            actor_user_id=admin.id,
            action="booking.confirm",
            resource_type="booking",
            resource_id=booking.id,
            request_id=request.state.request_id,
        )
        return booking
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found") from exc
    except booking_service.BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking cannot be confirmed") from exc


@router.patch("/bookings/{booking_id}/cancel", response_model=BookingRead)
def cancel_booking(
    booking_id: Annotated[int, Path(gt=0)],
    request: Request,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BookingRead:
    try:
        booking = booking_service.cancel_booking(db, booking_id)
        audit_service.record_event(
            db,
            actor_user_id=admin.id,
            action="booking.cancel",
            resource_type="booking",
            resource_id=booking.id,
            request_id=request.state.request_id,
        )
        return booking
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found") from exc
    except booking_service.BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is already cancelled") from exc


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(
    response: Response,
    pagination: Pagination = Depends(pagination_params),
    db: Session = Depends(get_db),
) -> list[AuditLogRead]:
    total = audit_service.count_events(db)
    add_pagination_headers(response, pagination=pagination, total=total)
    return audit_service.list_events(
        db, offset=pagination.offset, limit=pagination.per_page
    )


@router.get("/analytics", response_model=AdminAnalytics)
def analytics(
    on_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> AdminAnalytics:
    return AdminAnalytics(**booking_service.analytics_summary(db, on_date or date.today()))
