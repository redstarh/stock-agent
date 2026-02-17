"""테마 관련 Pydantic 스키마."""

from pydantic import BaseModel


class ThemeItem(BaseModel):
    """테마 강도 항목."""

    theme: str
    strength_score: float
    news_count: int
    sentiment_avg: float
    date: str
    market: str

    model_config = {"from_attributes": True}
