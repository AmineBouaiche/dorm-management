from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import CurrentUserRead, Token
from app.schemas.student import StudentCreate, StudentRead
from app.services import auth_service, student_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _student_to_read(student) -> StudentRead:
    return StudentRead(
        id=student.id,
        student_id=student.student_id,
        first_name=student.first_name,
        last_name=student.last_name,
        email=student.user.email,
    )


@router.post("/register", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def register_student(data: StudentCreate, db: Session = Depends(get_db)) -> StudentRead:
    try:
        return _student_to_read(student_service.create_student(db, data))
    except student_service.StudentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or student ID already exists",
        ) from exc


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    try:
        user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return Token(access_token=auth_service.issue_access_token(user))


@router.get("/me", response_model=CurrentUserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> CurrentUserRead:
    student = None
    if current_user.role == UserRole.STUDENT and current_user.student is not None:
        student = _student_to_read(current_user.student)
    return CurrentUserRead(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        student=student,
    )
