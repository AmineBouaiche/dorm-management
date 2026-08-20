from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_student
from app.db.database import get_db
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreate,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> BookingRead:
    try:
        return booking_service.create_booking(db, current_user.student, data)
    except booking_service.RoomNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found") from exc
    except booking_service.RoomUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is unavailable for this period") from exc
    except booking_service.StudentBookingConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student already has an overlapping booking",
        ) from exc


@router.get("/me", response_model=list[BookingRead])
def list_my_bookings(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> list[BookingRead]:
    return booking_service.list_student_bookings_by_db_id(db, current_user.student.id)


@router.patch("/{booking_id}/cancel", response_model=BookingRead)
def cancel_own_booking(
    booking_id: int,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> BookingRead:
    try:
        return booking_service.cancel_own_booking(db, booking_id, current_user.student.id)
    except booking_service.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found") from exc
    except booking_service.BookingOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another student's booking") from exc
    except booking_service.BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is already cancelled") from exc
