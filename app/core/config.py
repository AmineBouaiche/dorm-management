from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dorm Management System"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://dorm:dorm@localhost:5432/dorm_management"
    jwt_secret_key: SecretStr = SecretStr("development-only-change-this-secret-key")
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "dorm-management"
    jwt_audience: str = "dorm-management-web"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if not self.is_production:
            return self

        secret = self.jwt_secret_key.get_secret_value()
        weak_values = {
            "development-only-change-this-secret-key",
            "replace-with-a-long-random-secret",
        }
        if secret in weak_values or len(secret) < 32:
            raise ValueError("JWT_SECRET_KEY must be a unique secret of at least 32 characters in production")
        return self


settings = Settings()
