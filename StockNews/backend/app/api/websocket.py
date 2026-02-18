"""WebSocket 실시간 뉴스 스트림 엔드포인트."""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.redis import get_redis
from app.core.pubsub import subscribe_and_broadcast

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis 구독 태스크
_redis_task: asyncio.Task | None = None

MAX_WS_CONNECTIONS = 100

# 활성 연결 관리
_active_connections: list[WebSocket] = []


async def _add_connection(ws: WebSocket) -> bool:
    """연결 추가. 최대치 초과 시 False 반환."""
    if len(_active_connections) >= MAX_WS_CONNECTIONS:
        return False
    _active_connections.append(ws)
    return True


async def _remove_connection(ws: WebSocket):
    """연결 제거."""
    if ws in _active_connections:
        _active_connections.remove(ws)


async def broadcast(message: dict):
    """모든 활성 WebSocket에 메시지 브로드캐스트."""
    disconnected = []
    for ws in _active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        await _remove_connection(ws)


async def _start_redis_subscriber():
    """Redis 구독 시작 (백그라운드)."""
    global _redis_task
    if _redis_task is None or _redis_task.done():
        redis_client = get_redis()
        _redis_task = asyncio.create_task(
            subscribe_and_broadcast(redis_client, broadcast)
        )
        logger.info("Started Redis subscriber task")


async def _stop_redis_subscriber():
    """Redis 구독 중지."""
    global _redis_task
    if _redis_task and not _redis_task.done():
        _redis_task.cancel()
        try:
            await _redis_task
        except asyncio.CancelledError:
            pass
        logger.info("Stopped Redis subscriber task")


@router.websocket("/ws/news")
async def websocket_news(ws: WebSocket):
    """실시간 뉴스 WebSocket 엔드포인트."""
    await ws.accept()

    if not await _add_connection(ws):
        await ws.send_json({"type": "error", "message": "max connections exceeded"})
        await ws.close()
        return

    # Redis 구독 시작 (첫 클라이언트 연결 시)
    if len(_active_connections) == 1:
        await _start_redis_subscriber()

    # Welcome 메시지
    await ws.send_json({"type": "connected", "message": "StockNews WebSocket connected"})

    try:
        while True:
            data = await ws.receive_json()

            if data.get("type") == "ping":
                await ws.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
    finally:
        await _remove_connection(ws)

        # 마지막 클라이언트 연결 해제 시 Redis 구독 중지
        if len(_active_connections) == 0:
            await _stop_redis_subscriber()
