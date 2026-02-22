"""FastAPI 애플리케이션 엔트리포인트."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import app.models  # noqa: F401 — register all models with Base.metadata
from app.api.health import router as health_router
from app.api.prediction import router as prediction_router
from app.api.router import api_v1_router, api_v2_router
from app.api.scheduler import router as scheduler_router
from app.api.strategy import router as strategy_router
from app.api.summary import router as summary_router
from app.api.versions import router as versions_router
from app.api.websocket import router as ws_router
from app.core.config import settings
from app.core.database import engine
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.monitoring import init_sentry, sanitize_exception_message, setup_prometheus
from app.core.versioning import APIVersionMiddleware
from app.models.base import Base

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """애플리케이션 시작/종료 이벤트."""
    # Startup: Configure structured logging
    setup_logging(
        log_level=settings.log_level,
        json_output=(settings.app_env != "development"),
        app_env=settings.app_env,
    )

    # Startup: Initialize Sentry
    init_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        debug=settings.debug,
    )

    # Startup: 테이블 생성 (MVP — production에서는 Alembic 사용)
    Base.metadata.create_all(bind=engine)

    # Startup: 초기 전략 시딩 (V1)
    from app.core.database import SessionLocal
    from app.processing.strategy_config import StrategyConfig
    from app.processing.strategy_registry import StrategyRegistry

    strategy_db = SessionLocal()
    try:
        registry = StrategyRegistry()
        active = registry.get_active("KR", strategy_db)
        if not active:
            v1 = StrategyConfig.default_v1()
            sid = registry.save(v1, "KR", strategy_db)
            registry.activate(sid, strategy_db)
            # Also seed for US market
            us_sid = registry.save(v1, "US", strategy_db)
            registry.activate(us_sid, strategy_db)
            logger.info("Seeded default V1 strategy for KR and US markets")
        else:
            logger.info("Active strategy already exists: %s v%s", active.strategy_name, active.strategy_version)
    except Exception as e:
        logger.warning("Strategy seeding failed: %s", e)
    finally:
        strategy_db.close()

    # Startup: 수집 스케줄러 시작
    from app.collectors.scheduler import create_scheduler, run_startup_catchup
    from app.collectors.verification_scheduler import register_verification_jobs
    from app.core.scheduler_state import set_scheduler

    scheduler = create_scheduler()
    register_verification_jobs(scheduler)
    scheduler.start()
    set_scheduler(scheduler)
    logger.info("News collection scheduler started")
    logger.info("Verification scheduler jobs registered")

    # Startup: 08:00 KST 이후 서버 시작 시 캐치업 (종목 선정 → 수집 → 예측)
    run_startup_catchup()

    yield

    # Shutdown: 스케줄러 종료
    scheduler.shutdown(wait=False)
    logger.info("News collection scheduler stopped")


app = FastAPI(
    title="StockNews API",
    description="News Intelligence Service for Stock Markets",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiter setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
)

# Request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# API version middleware
app.add_middleware(APIVersionMiddleware)

# Routers
app.include_router(health_router)
app.include_router(versions_router)
app.include_router(api_v1_router)
app.include_router(api_v2_router)
app.include_router(prediction_router)
app.include_router(strategy_router)
app.include_router(summary_router)
app.include_router(scheduler_router, prefix="/api/v1")
app.include_router(ws_router)

# Prometheus metrics (after routers to avoid middleware interference)
if settings.enable_metrics:
    setup_prometheus(app)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러."""
    # Log the exception
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Return sanitized error message
    error_message = sanitize_exception_message(exc, settings.debug)

    return JSONResponse(
        status_code=500,
        content={"detail": error_message, "status_code": 500},
    )
