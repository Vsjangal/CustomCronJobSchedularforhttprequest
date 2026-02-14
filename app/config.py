from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./api_scheduler.db"
    scheduler_poll_seconds: float = 1.0
    default_request_timeout: int = 30
    max_concurrent_executions: int = 50

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
