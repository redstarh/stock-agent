"""스케줄러 관리 API."""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core.auth import verify_api_key
from app.core.limiter import limiter
from app.core.scheduler_state import get_job_history, get_scheduler
from app.schemas.scheduler import (
    SchedulerJobHistoryItem,
    SchedulerJobHistoryResponse,
    SchedulerJobInfo,
    SchedulerJobListResponse,
    SchedulerJobTriggerResponse,
)

logger = logging.getLogger(__name__)

# Job metadata (static descriptions)
JOB_METADATA = {
    "kr_news_collection": {
        "name": "한국 뉴스 수집",
        "job_type": "collection",
        "schedule_description": "5분 간격",
    },
    "dart_disclosure_collection": {
        "name": "DART 공시 수집",
        "job_type": "collection",
        "schedule_description": "5분 간격",
    },
    "us_news_collection": {
        "name": "미국 뉴스 수집",
        "job_type": "collection",
        "schedule_description": "5분 간격",
    },
    "daily_stock_selection": {
        "name": "일일 종목 선정",
        "job_type": "selection",
        "schedule_description": "평일 08:00 KST (23:00 UTC)",
    },
    "kr_verification": {
        "name": "한국 시장 검증",
        "job_type": "verification",
        "schedule_description": "평일 06:35 UTC (15:35 KST)",
    },
    "us_verification": {
        "name": "미국 시장 검증",
        "job_type": "verification",
        "schedule_description": "평일 21:30 UTC (16:30 EST)",
    },
}

router = APIRouter(
    prefix="/scheduler",
    tags=["scheduler"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/jobs", response_model=SchedulerJobListResponse)
@limiter.limit("60/minute")
async def list_jobs(request: Request, response: Response):
    """전체 스케줄 작업 목록 조회."""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    jobs = []
    for job in scheduler.get_jobs():
        meta = JOB_METADATA.get(
            job.id,
            {
                "name": job.id,
                "job_type": "unknown",
                "schedule_description": str(job.trigger),
            },
        )
        trigger_type = "cron" if "cron" in str(type(job.trigger)).lower() else "interval"
        jobs.append(
            SchedulerJobInfo(
                job_id=job.id,
                name=meta["name"],
                job_type=meta["job_type"],
                trigger_type=trigger_type,
                schedule_description=meta["schedule_description"],
                next_run_time=job.next_run_time,
                is_running=False,  # APScheduler doesn't track this directly
            )
        )

    return SchedulerJobListResponse(
        jobs=jobs,
        scheduler_running=scheduler.running,
    )


@router.post("/jobs/{job_id}/trigger", response_model=SchedulerJobTriggerResponse)
@limiter.limit("10/minute")
async def trigger_job(request: Request, response: Response, job_id: str):
    """스케줄 작업 수동 실행."""
    scheduler = get_scheduler()
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")

    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    # Trigger immediate execution
    job.modify(next_run_time=datetime.now(UTC))
    meta = JOB_METADATA.get(job_id, {"name": job_id})

    return SchedulerJobTriggerResponse(
        job_id=job_id,
        status="triggered",
        message=f"'{meta['name']}' 작업이 즉시 실행됩니다.",
    )


@router.get("/jobs/{job_id}/history", response_model=SchedulerJobHistoryResponse)
@limiter.limit("60/minute")
async def get_job_history_endpoint(request: Request, response: Response, job_id: str):
    """스케줄 작업 실행 이력 조회."""
    history = get_job_history(job_id)
    return SchedulerJobHistoryResponse(
        job_id=job_id,
        history=[SchedulerJobHistoryItem(**h) for h in history],
    )
