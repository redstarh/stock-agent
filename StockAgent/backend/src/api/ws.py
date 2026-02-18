"""WebSocket 실시간 API"""

from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="", tags=["websocket"])

# 연결된 클라이언트 관리
active_connections: Set[WebSocket] = set()


@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """실시간 데이터 WebSocket 엔드포인트"""
    await websocket.accept()
    active_connections.add(websocket)

    try:
        # 연결 시 시스템 상태 전송
        await websocket.send_json({
            "type": "system_status",
            "status": "connected",
            "timestamp": "2026-02-18T00:00:00",
        })

        # 클라이언트 메시지 수신 대기
        while True:
            # 클라이언트로부터 메시지 수신 (ping/pong 등)
            data = await websocket.receive_text()
            # Echo back or handle commands
            await websocket.send_json({
                "type": "ack",
                "message": f"Received: {data}",
            })

    except WebSocketDisconnect:
        active_connections.discard(websocket)


async def broadcast(message: dict):
    """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
    disconnected = set()
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.add(connection)

    # 연결 해제된 클라이언트 제거
    active_connections.difference_update(disconnected)
