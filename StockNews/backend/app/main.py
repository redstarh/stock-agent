"""FastAPI 애플리케이션 엔트리포인트."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.prediction import router as prediction_router
from app.api.router import api_v1_router
from app.api.summary import router as summary_router
from app.api.websocket import router as ws_router
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
import app.models  # noqa: F401 — register all models with Base.metadata


@asynccontextmanager
async def lifespan(application: FastAPI):
    """애플리케이션 시작/종료 이벤트."""
    # Startup: 테이블 생성 (MVP — production에서는 Alembic 사용)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="StockNews API",
    description="News Intelligence Service for Stock Markets",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(api_v1_router)
app.include_router(prediction_router)
app.include_router(summary_router)
app.include_router(ws_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러."""
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "status_code": 500},
    )
