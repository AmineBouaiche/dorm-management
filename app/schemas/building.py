from pydantic import BaseModel, ConfigDict, Field


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    address: str = Field(min_length=1, max_length=255)
    image_url: str | None = Field(default=None, max_length=500)


class BuildingUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class BuildingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: str
    image_url: str | None
    is_active: bool
