"""Health check 엔드포인트."""

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 + DB/Redis 연결 확인."""
    status = {"status": "ok", "services": {}}

    # DB check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["services"]["database"] = "ok"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "degraded"

    # Redis check
    try:
        import redis

        r = redis.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        status["services"]["redis"] = "ok"
    except Exception:
        status["services"]["redis"] = "unavailable"
        # Redis is optional for MVP, don't degrade status

    return HealthResponse(
        status=status["status"],
        version="0.1.0",
        services=status["services"],
    )
