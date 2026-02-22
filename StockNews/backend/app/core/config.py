"""Pydantic Settings 기반 환경 설정."""

import os
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정."""

    # Secrets Manager
    secrets_provider: str = ""  # "", "aws", "file"
    secrets_name: str = ""  # AWS SM secret name or file path
    secrets_region: str = ""  # AWS region for Secrets Manager

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
    collection_interval_kr: int = 5  # Korean news (Naver/RSS)
    collection_interval_dart: int = 5  # DART disclosures (rate limited)
    collection_interval_us: int = 5  # US news (Finnhub)

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


def _load_settings_with_secrets() -> Settings:
    """Secrets Manager 통합을 포함한 설정을 로드합니다."""
    # 기본 설정 로드
    base_settings = Settings()

    # Secrets provider가 설정되지 않은 경우 기본 동작 유지
    if not base_settings.secrets_provider:
        return base_settings

    # Secrets provider 초기화
    try:
        from app.core.secrets import create_secrets_provider

        provider = create_secrets_provider(
            base_settings.secrets_provider,
            secret_name=base_settings.secrets_name,
            file_path=base_settings.secrets_name,  # file provider용
            region_name=base_settings.secrets_region,
        )

        # 민감한 필드 목록 (secrets provider에서 우선 조회)
        sensitive_fields = [
            "api_key",
            "api_key_next",
            "openai_api_key",
            "aws_access_key_id",
            "aws_secret_access_key",
            "dart_api_key",
            "finnhub_api_key",
            "newsapi_api_key",
            "redis_password",
            "database_url",
            "sentry_dsn",
        ]

        # Secrets provider에서 값 조회 및 오버라이드
        overrides: dict[str, Any] = {}
        for field in sensitive_fields:
            secret_value = provider.get_secret(field)
            if secret_value:
                overrides[field] = secret_value

        # 오버라이드가 있으면 새 Settings 인스턴스 생성
        if overrides:
            # 환경 변수 임시 업데이트 (pydantic-settings는 env를 우선 조회)
            original_env = {}
            for key, value in overrides.items():
                env_key = key.upper()
                original_env[env_key] = os.environ.get(env_key)
                os.environ[env_key] = value

            # 새 Settings 인스턴스 생성
            updated_settings = Settings()

            # 원래 환경 변수 복원
            for key in overrides:
                env_key = key.upper()
                if original_env[env_key] is None:
                    os.environ.pop(env_key, None)
                else:
                    os.environ[env_key] = original_env[env_key]

            return updated_settings

    except Exception as e:
        # Secrets provider 로드 실패 시 경고 출력하고 기본 설정 사용
        print(f"Warning: Secrets provider failed, using default settings: {e}")

    return base_settings


settings = _load_settings_with_secrets()
