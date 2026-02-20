"""뉴스 요약 API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import verify_api_key
from app.processing.summary import summarize_news

router = APIRouter(
    prefix="/api/v1",
    tags=["summary"],
    dependencies=[Depends(verify_api_key)],
)


class SummarizeRequest(BaseModel):
    title: str
    body: str | None = None


class SummarizeResponse(BaseModel):
    summary: str


@router.post("/news/summarize", response_model=SummarizeResponse)
async def create_summary(req: SummarizeRequest) -> SummarizeResponse:
    summary = summarize_news(req.title, req.body)
    return SummarizeResponse(summary=summary)
