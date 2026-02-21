"""Pydantic Settings 기반 환경 설정."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정."""

    # Database
    database_url: str = "sqlite+aiosqlite:///./stocknews.db"
    database_ssl_mode: str = ""  # "", "require", "verify-ca", "verify-full"
    database_ssl_ca: str = ""  # Path to CA certificate

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""
    redis_ssl: bool = False
    redis_ssl_ca: str = ""  # Path to CA certificate

    # OpenAI
    openai_api_key: str = ""

    # AWS Bedrock
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_profile: str = ""
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    bedrock_model_id_fast: str = ""
    bedrock_model_id_mid: str = ""

    # DART
    dart_api_key: str = ""

    # US News APIs
    finnhub_api_key: str = ""
    newsapi_api_key: str = ""

    # App
    app_env: str = "development"
    debug: bool = True
    log_level: str = "DEBUG"

    # Collection Intervals (minutes)
    collection_interval_kr: int = 1  # Korean news (Naver/RSS)
    collection_interval_dart: int = 5  # DART disclosures (rate limited)
    collection_interval_us: int = 3  # US news (Finnhub/NewsAPI)

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Authentication
    api_key: str = "dev-api-key-change-in-production"
    api_key_next: str = ""  # Next key for rotation (both current and next are valid)
    require_auth: bool = False

    # Monitoring
    sentry_dsn: str = ""
    enable_metrics: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
