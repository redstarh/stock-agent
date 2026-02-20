"""API 인증 미들웨어 및 종속성."""

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/metrics",
}


def is_public_endpoint(path: str) -> bool:
    """Check if the endpoint is public."""
    return path in PUBLIC_ENDPOINTS or path.startswith("/docs") or path.startswith("/redoc")


async def verify_api_key(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> str | None:
    """
    API Key 검증 종속성.

    - Development 모드에서는 인증 스킵
    - Public 엔드포인트는 인증 스킵
    - require_auth=False인 경우 인증 스킵
    - 그 외 경우 X-API-Key 헤더 검증
    """
    # Skip auth in development mode
    if settings.app_env == "development":
        return None

    # Skip auth if not required in settings
    if not settings.require_auth:
        return None

    # Skip auth for public endpoints
    if is_public_endpoint(request.url.path):
        return None

    # Verify API key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return api_key
