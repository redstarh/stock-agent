"""API 버전 관리 미들웨어 및 유틸리티."""

from collections.abc import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API 버전 헤더를 추가하는 미들웨어."""

    # RFC 8594 Sunset 날짜 (v1 지원 종료 예정일)
    V1_SUNSET_DATE = "Sat, 31 Dec 2026 23:59:59 GMT"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """요청 처리 및 버전 헤더 추가."""
        response = await call_next(request)

        # API 경로인지 확인
        path = request.url.path
        if not path.startswith("/api/"):
            return response

        # 버전 감지
        if path.startswith("/api/v1/"):
            version = "v1"
            # v1은 deprecated 상태
            response.headers["X-API-Version"] = version
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = self.V1_SUNSET_DATE
            response.headers["Link"] = f'<{path.replace("/api/v1/", "/api/v2/")}>; rel="successor-version"'
        elif path.startswith("/api/v2/"):
            version = "v2"
            response.headers["X-API-Version"] = version
        else:
            # /api/versions 등 버전 없는 엔드포인트
            return response

        return response


def get_api_versions() -> dict:
    """사용 가능한 API 버전 목록 반환."""
    sunset_date = datetime.strptime(
        APIVersionMiddleware.V1_SUNSET_DATE,
        "%a, %d %b %Y %H:%M:%S %Z"
    )

    return {
        "versions": [
            {
                "version": "v1",
                "status": "deprecated",
                "base_url": "/api/v1",
                "sunset_date": sunset_date.isoformat(),
                "successor": "v2"
            },
            {
                "version": "v2",
                "status": "stable",
                "base_url": "/api/v2",
                "sunset_date": None,
                "successor": None
            }
        ],
        "default_version": "v2",
        "recommended_version": "v2"
    }
