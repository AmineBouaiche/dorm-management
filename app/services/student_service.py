from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.student import Student
from app.models.user import User
from app.schemas.student import StudentCreate


class StudentNotFoundError(Exception):
    pass


class StudentAlreadyExistsError(Exception):
    pass


def _student_query():
    return select(Student).options(joinedload(Student.user))


def list_students(db: Session) -> list[Student]:
    statement = _student_query().order_by(Student.student_id)
    return list(db.scalars(statement).all())


def get_student(db: Session, student_id: str) -> Student:
    statement = _student_query().where(Student.student_id == student_id.strip())
    student = db.scalar(statement)
    if student is None:
        raise StudentNotFoundError
    return student


def create_student(db: Session, data: StudentCreate) -> Student:
    normalized_email = str(data.email).strip().lower()
    normalized_student_id = data.student_id.strip()

    user = User(
        email=normalized_email,
        password_hash=hash_password(data.password),
        role=UserRole.STUDENT,
    )
    try:
        db.add(user)
        db.flush()

        student = Student(
            user_id=user.id,
            student_id=normalized_student_id,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
        )
        db.add(student)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise StudentAlreadyExistsError from exc

    return get_student(db, normalized_student_id)
