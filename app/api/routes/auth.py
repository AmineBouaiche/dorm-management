import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import (
    AUTH_RATE_LIMITER,
    LOGIN_ACCOUNT_RULE,
    LOGIN_IP_RULE,
    REGISTER_IP_RULE,
)
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


def _current_user_to_read(current_user: User) -> CurrentUserRead:
    student = None
    if current_user.role == UserRole.STUDENT and current_user.student is not None:
        student = _student_to_read(current_user.student)
    return CurrentUserRead(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        student=student,
    )


def _client_ip(request: Request) -> str:
    # Do not trust X-Forwarded-For until the deployment proxy topology is explicitly configured.
    return request.client.host if request.client is not None else "unknown"


def _login_keys(request: Request, username: str) -> tuple[str, str]:
    normalized = username.strip().lower()[:254]
    return f"login:ip:{_client_ip(request)}", f"login:account:{normalized}"


def _raise_rate_limited(retry_after: int) -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Try again later.",
        headers={"Retry-After": str(retry_after)},
    )


def _precheck_login_rate_limit(request: Request, username: str) -> tuple[str, str]:
    ip_key, account_key = _login_keys(request, username)
    retry_after = AUTH_RATE_LIMITER.retry_after(ip_key, LOGIN_IP_RULE)
    if retry_after is None:
        retry_after = AUTH_RATE_LIMITER.retry_after(account_key, LOGIN_ACCOUNT_RULE)
    if retry_after is not None:
        _raise_rate_limited(retry_after)
    return ip_key, account_key


def _validate_login_fields(username: str, password: str) -> None:
    if not username or len(username) > 254 or len(password) > 128:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid login input")


def _authenticate(
    request: Request,
    form_data: OAuth2PasswordRequestForm,
    db: Session,
) -> User:
    _validate_login_fields(form_data.username, form_data.password)
    ip_key, account_key = _precheck_login_rate_limit(request, form_data.username)
    try:
        user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    except auth_service.InvalidCredentialsError as exc:
        ip_retry = AUTH_RATE_LIMITER.record(ip_key, LOGIN_IP_RULE)
        account_retry = AUTH_RATE_LIMITER.record(account_key, LOGIN_ACCOUNT_RULE)
        retry_after = account_retry or ip_retry
        if retry_after is not None:
            _raise_rate_limited(retry_after)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    AUTH_RATE_LIMITER.clear(account_key)
    return user


def _set_session_cookies(response: Response, token: str) -> None:
    max_age = settings.access_token_expire_minutes * 60
    secure = settings.is_production
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=secure,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=secrets.token_urlsafe(32),
        max_age=max_age,
        httponly=False,
        secure=secure,
        samesite="strict",
        path="/",
    )


@router.post("/register", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def register_student(
    data: StudentCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> StudentRead:
    registration_key = f"register:ip:{_client_ip(request)}"
    retry_after = AUTH_RATE_LIMITER.retry_after(registration_key, REGISTER_IP_RULE)
    if retry_after is not None:
        _raise_rate_limited(retry_after)
    AUTH_RATE_LIMITER.record(registration_key, REGISTER_IP_RULE)
    try:
        return _student_to_read(student_service.create_student(db, data))
    except student_service.StudentAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or student ID already exists",
        ) from exc


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> Token:
    """Bearer-token login retained for development tooling and API clients."""
    user = _authenticate(request, form_data, db)
    return Token(access_token=auth_service.issue_access_token(user))


@router.post("/session", response_model=CurrentUserRead)
def create_browser_session(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> CurrentUserRead:
    """Create an HttpOnly browser session without exposing the JWT to JavaScript."""
    user = _authenticate(request, form_data, db)
    _set_session_cookies(response, auth_service.issue_access_token(user))
    return _current_user_to_read(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    response.delete_cookie(settings.auth_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=CurrentUserRead)
def read_current_user(current_user: User = Depends(get_current_user)) -> CurrentUserRead:
    return _current_user_to_read(current_user)
