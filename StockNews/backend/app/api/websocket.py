"""WebSocket 실시간 뉴스 스트림 엔드포인트."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

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


@router.websocket("/ws/news")
async def websocket_news(ws: WebSocket):
    """실시간 뉴스 WebSocket 엔드포인트."""
    await ws.accept()

    if not await _add_connection(ws):
        await ws.send_json({"type": "error", "message": "max connections exceeded"})
        await ws.close()
        return

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
