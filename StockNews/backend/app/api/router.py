"""API v1 라우터 — 모든 엔드포인트 통합."""

from fastapi import APIRouter

from app.api.collect import router as collect_router
from app.api.news import router as news_router
from app.api.stocks import router as stocks_router
from app.api.themes import router as themes_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(collect_router)
api_v1_router.include_router(news_router)
api_v1_router.include_router(stocks_router)
api_v1_router.include_router(themes_router)
