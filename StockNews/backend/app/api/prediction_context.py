"""예측 컨텍스트 API 엔드포인트."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.core.limiter import limiter
from app.processing.llm_predictor import predict_with_llm
from app.processing.prediction_context_builder import (
    DEFAULT_CONTEXT_PATH,
    build_and_save_prediction_context,
)
from app.schemas.prediction_context import (
    ContextRebuildResponse,
    LLMPredictionResponse,
    PredictionContextResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prediction-context",
    tags=["prediction-context"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=PredictionContextResponse)
@limiter.limit("60/minute")
async def get_prediction_context(
    request: Request,
    response: Response,
    market: str | None = Query(None, description="KR or US (optional)"),
):
    """현재 예측 컨텍스트 조회."""
    try:
        with open(DEFAULT_CONTEXT_PATH, encoding="utf-8") as f:
            context = json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Prediction context not found. Run POST /prediction-context/rebuild first.",
        ) from None
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Prediction context file is corrupted.",
        ) from None

    # If market filter is specified, filter market_conditions
    if market:
        context["market_conditions"] = [
            mc for mc in context.get("market_conditions", [])
            if mc["market"] == market
        ]

    return PredictionContextResponse(**context)


@router.post("/rebuild", response_model=ContextRebuildResponse)
@limiter.limit("10/minute")
async def rebuild_prediction_context(
    request: Request,
    response: Response,
    days: int = Query(30, description="분석 기간 (일)", ge=1, le=365),
    market: str | None = Query(None, description="KR or US (optional)"),
    db: Session = Depends(get_db),
):
    """예측 컨텍스트 리빌드."""
    context = build_and_save_prediction_context(db, days=days, output_path=DEFAULT_CONTEXT_PATH)

    return ContextRebuildResponse(
        success=True,
        version=context["version"],
        analysis_days=context["analysis_days"],
        total_predictions=context["total_predictions"],
        overall_accuracy=context["overall_accuracy"],
        file_path=DEFAULT_CONTEXT_PATH,
        generated_at=context["generated_at"],
    )


# This endpoint is under /stocks/{code}/prediction/llm but we mount it
# via a separate router to keep the prefix clean
prediction_llm_router = APIRouter(
    prefix="/stocks",
    tags=["prediction-context"],
    dependencies=[Depends(verify_api_key)],
)


@prediction_llm_router.get(
    "/{code}/prediction/llm", response_model=LLMPredictionResponse
)
@limiter.limit("30/minute")
async def get_llm_prediction(
    request: Request,
    response: Response,
    code: str,
    market: str = Query("KR", description="KR or US"),
    db: Session = Depends(get_db),
):
    """LLM 기반 주가 예측."""
    result = predict_with_llm(db, code, market)
    return result
