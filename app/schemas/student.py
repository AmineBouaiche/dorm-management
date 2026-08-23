from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StudentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    student_id: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9-]+$")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    @field_validator("first_name", "last_name")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 for char in value):
            raise ValueError("Name contains invalid control characters")
        return value


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: str
    first_name: str
    last_name: str
    email: EmailStr
