"""API 버전 정보 엔드포인트."""

from fastapi import APIRouter

from app.core.versioning import get_api_versions

router = APIRouter(tags=["versions"])


@router.get("/api/versions")
def list_api_versions():
    """
    사용 가능한 API 버전 목록 조회.

    Returns:
        dict: API 버전 정보
            - versions: 버전 목록 (version, status, base_url, sunset_date, successor)
            - default_version: 기본 버전
            - recommended_version: 권장 버전
    """
    return get_api_versions()
