from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://pnw:pnw_dev_password@localhost:5432/pnw_chatbot"
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173"]
    )
    request_max_bytes: int = Field(default=16_384, gt=0)
    anonymous_rate_limit_per_minute: int = Field(default=20, gt=0)
    gemini_api_key: SecretStr | None = None
    gemini_model: str = Field(default="gemini-2.0-flash", min_length=1)
    gemini_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    gemini_timeout_seconds: float = Field(default=30.0, gt=0.0)
    embedding_model: str = Field(default="text-embedding-004", min_length=1)
    embedding_dimension: int = Field(default=768, gt=0)
    source_review_window_days: int = Field(default=180, gt=0)
    conversation_ttl_seconds: int = Field(default=1800, gt=0)

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return [origin.strip() for origin in value if origin.strip()]

    @field_validator("gemini_api_key", mode="before")
    @classmethod
    def empty_api_key_is_none(cls, value: str | SecretStr | None) -> str | SecretStr | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


settings = Settings()
