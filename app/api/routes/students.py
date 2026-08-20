from fastapi import APIRouter, Depends

from app.api.dependencies import require_student
from app.models.user import User
from app.schemas.student import StudentRead

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=StudentRead)
def get_my_student_profile(current_user: User = Depends(require_student)) -> StudentRead:
    student = current_user.student
    return StudentRead(
        id=student.id,
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.user.email,
    )
