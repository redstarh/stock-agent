"""수집 품질 모니터링 응답 스키마."""

from pydantic import BaseModel


class SourceQualityStats(BaseModel):
    """소스별 품질 통계."""
    total_items: int
    scrape_success_rate: float
    avg_confidence: float
    neutral_ratio: float
    avg_news_score: float
    high_score_ratio: float
    last_updated: str | None


class QualitySummary(BaseModel):
    """전체 품질 요약."""
    total_sources: int
    total_items_tracked: int
    overall_scrape_success_rate: float
    overall_avg_confidence: float


class CollectionQualityResponse(BaseModel):
    """수집 품질 API 응답."""
    summary: QualitySummary
    sources: dict[str, SourceQualityStats]
