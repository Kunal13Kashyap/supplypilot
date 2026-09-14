from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    demo_mode: bool = True
    mock_llm: bool = True
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    web_origin: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    jwt_secret: str = "change-me-in-any-non-demo-environment"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "procureai"
    postgres_user: str = "procureai"
    postgres_password: str = "procureai"
    database_url: str = "postgresql+asyncpg://procureai:procureai@localhost:5432/procureai"

    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    llm_timeout_seconds: int = 30

    approval_amount_medium: float = 1000
    approval_amount_high: float = 5000
    target_stock_default: float = 200
    embedding_dimensions: int = 1536

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def use_mock_llm(self) -> bool:
        return self.mock_llm or not self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
