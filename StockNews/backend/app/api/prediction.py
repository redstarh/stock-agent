"""Prediction API endpoints."""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.limiter import limiter

from app.core.database import get_db
from app.models.news_event import NewsEvent
from app.schemas.prediction import PredictionResponse

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.get("/stocks/{code}/prediction", response_model=PredictionResponse)
@limiter.limit("60/minute")
async def get_prediction(request: Request, response: Response, code: str, db: Session = Depends(get_db)):
    """종목별 예측 점수 반환.

    실제 구현에서는 DB에서 최근 뉴스를 조회하여 피처를 추출하고
    학습된 모델로 예측합니다. MVP에서는 뉴스 스코어 기반 heuristic.

    Args:
        code: 종목 코드
        db: Database session

    Returns:
        PredictionResponse with prediction_score, direction, confidence
    """
    # 최근 30일 뉴스 조회 (최대 100개)
    news = (
        db.query(NewsEvent)
        .filter(NewsEvent.stock_code == code)
        .order_by(NewsEvent.created_at.desc())
        .limit(100)
        .all()
    )

    if not news:
        return PredictionResponse(stock_code=code)

    # 피처 추출
    avg_score = sum(n.news_score for n in news) / len(news)
    avg_sentiment = sum(n.sentiment_score for n in news) / len(news)
    news_count = len(news)

    # Heuristic prediction (MVP - no trained model needed)
    # prediction_score: 0-100 scale
    # Formula: weighted average of news_score and normalized sentiment
    prediction_score = min(100, max(0, avg_score * 0.6 + (avg_sentiment + 1) * 20))

    # Direction based on prediction score
    if prediction_score > 60:
        direction = "up"
    elif prediction_score < 40:
        direction = "down"
    else:
        direction = "neutral"

    # Confidence based on news volume and score extremity
    # More news = higher confidence (up to 50% contribution)
    # More extreme score = higher confidence (up to 50% contribution)
    volume_confidence = min(1.0, news_count / 20) * 0.5
    extremity_confidence = abs(prediction_score - 50) / 100
    confidence = volume_confidence + extremity_confidence

    return PredictionResponse(
        stock_code=code,
        prediction_score=round(prediction_score, 1),
        direction=direction,
        confidence=round(min(1.0, confidence), 2),
        based_on_days=30,
    )
