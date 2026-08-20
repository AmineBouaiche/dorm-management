from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StudentCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    student_id: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: str
    first_name: str
    last_name: str
    email: EmailStr
