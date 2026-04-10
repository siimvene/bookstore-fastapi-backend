from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "bookstore-service"
    app_title: str = "Bookstore API"
    app_description: str = "REST API for Bookstore Application"
    app_version: str = "1.0.0"
    api_prefix: str = "/api"

    # Server
    server_port: int = 8080

    # Database
    datasource_url: str = "postgresql+asyncpg://localhost:5432/bookstore"
    db_pool_max_size: int = 5
    db_pool_min_idle: int = 1
    db_pool_overflow: int = 10

    # OAuth2 / JWT
    oauth2_jwk_uri: str = ""
    oauth2_issuer_uri: str = ""
    oauth2_audience: str = "bookstore-api"

    # API Documentation
    enable_swagger_ui: bool = Field(default=False)
    enable_api_docs: bool = Field(default=False)

    # Logging
    log_level: str = "INFO"
    app_log_level: str = "DEBUG"
    log_json: bool = True

    # Retry
    retry_max_attempts: int = 3
    retry_initial_backoff_ms: int = 500
    retry_max_backoff_ms: int = 5000
    retry_multiplier: float = 2.0

    # Problem Details
    problem_base_uri: str = "https://api.example.com/errors"

    # Audit
    audit_logger_name: str = "audit"
    audit_client_id: str = "bookstore-app"
    environment: str = "dev"

    # OpenTelemetry
    otel_enabled: bool = False
    otel_service_name: str = "bookstore-service"
    otel_exporter_endpoint: str = "http://localhost:4317"

    # CORS
    cors_origins: list[str] = []
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
