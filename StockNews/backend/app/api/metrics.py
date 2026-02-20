"""Prometheus metrics endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["metrics"])


# The metrics endpoint is exposed by the Instrumentator
# This router is for documentation purposes and future custom metrics
@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint.

    This endpoint is automatically handled by prometheus-fastapi-instrumentator.
    It exposes standard HTTP metrics and custom application metrics.
    """
    pass  # Instrumentator handles this
