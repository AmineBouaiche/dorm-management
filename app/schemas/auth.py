from pydantic import BaseModel

from app.models.enums import UserRole
from app.schemas.student import StudentRead


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserRead(BaseModel):
    id: int
    email: str
    role: UserRole
    student: StudentRead | None = None
