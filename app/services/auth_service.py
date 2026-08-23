from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import (
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
)
from app.models.student import Student
from app.models.user import User


class InvalidCredentialsError(Exception):
    pass


def authenticate_user(db: Session, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    statement = select(User).options(joinedload(User.student)).where(User.email == normalized_email)
    user = db.scalar(statement)
    if user is None:
        verify_dummy_password(password)
        raise InvalidCredentialsError
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(user.id)


def get_user_with_student(db: Session, user_id: int) -> User | None:
    statement = (
        select(User)
        .options(joinedload(User.student).joinedload(Student.user))
        .where(User.id == user_id)
    )
    return db.scalar(statement)
