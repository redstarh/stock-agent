"""API v2 라우터 — v1 엔드포인트를 재사용하며 향후 분기 가능."""

from fastapi import APIRouter

from app.api.collect import router as collect_router
from app.api.news import router as news_router
from app.api.prediction_context import prediction_llm_router
from app.api.prediction_context import router as prediction_context_router
from app.api.stocks import router as stocks_router
from app.api.themes import router as themes_router
from app.api.training import router as training_router
from app.api.verification import router as verification_router

api_v2_router = APIRouter(prefix="/api/v2")

# v2는 현재 v1 엔드포인트를 재사용 (향후 분기 시 별도 구현 가능)
api_v2_router.include_router(collect_router)
api_v2_router.include_router(news_router)
api_v2_router.include_router(stocks_router)
api_v2_router.include_router(themes_router)
api_v2_router.include_router(training_router)
api_v2_router.include_router(verification_router)
api_v2_router.include_router(prediction_context_router)
api_v2_router.include_router(prediction_llm_router)
