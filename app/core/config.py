from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Dorm Management System"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://dorm:dorm@localhost:5432/dorm_management"
    jwt_secret_key: str = "development-only-change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
