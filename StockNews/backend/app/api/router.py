"""API 라우터 — v1 및 v2 엔드포인트 통합."""

from fastapi import APIRouter

from app.api.collect import router as collect_router
from app.api.news import router as news_router
from app.api.stocks import router as stocks_router
from app.api.themes import router as themes_router
from app.api.training import router as training_router
from app.api.verification import router as verification_router
from app.api.prediction_context import router as prediction_context_router
from app.api.prediction_context import prediction_llm_router
from app.advan.api import router as advan_router

# API v1 라우터
api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(collect_router)
api_v1_router.include_router(news_router)
api_v1_router.include_router(stocks_router)
api_v1_router.include_router(themes_router)
api_v1_router.include_router(training_router)
api_v1_router.include_router(verification_router)
api_v1_router.include_router(prediction_context_router)
api_v1_router.include_router(prediction_llm_router)
api_v1_router.include_router(advan_router)

# API v2 라우터 (v2 패키지에서 임포트)
from app.api.v2.router import api_v2_router  # noqa: E402

__all__ = ["api_v1_router", "api_v2_router"]
