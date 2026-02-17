"""Health check 엔드포인트."""

from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 확인."""
    return HealthResponse(status="ok", version="0.1.0")
