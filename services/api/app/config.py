"""Application configuration loaded from environment or .env file."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg://trackflow:trackflow@localhost:5432/trackflow"
    )
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    telemetry_endpoint: str | None = None
    supabase_telemetry_url: str = (
        "https://stkmiwhfkrfksraszovd.supabase.co/rest/v1/telemetry_events"
    )
    supabase_service_role_key: str | None = Field(default=None, repr=False)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()