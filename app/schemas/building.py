from pydantic import BaseModel, ConfigDict, Field, field_validator


class BuildingBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    @field_validator("image_url", check_fields=False)
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value.startswith("/static/assets/residences/") or value.startswith("https://"):
            return value
        raise ValueError("image_url must be an HTTPS URL or a local residence asset path")


class BuildingCreate(BuildingBase):
    name: str = Field(min_length=1, max_length=150)
    address: str = Field(min_length=1, max_length=255)
    image_url: str | None = Field(default=None, max_length=500)


class BuildingUpdate(BuildingBase):
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
