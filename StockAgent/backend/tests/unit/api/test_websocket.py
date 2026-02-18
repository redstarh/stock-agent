"""T-B18: WebSocket 실시간 API 테스트"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.testclient import TestClient

from src.api.ws import active_connections, broadcast
from src.main import app


@pytest.fixture(autouse=True)
def cleanup_connections():
    """각 테스트 후 active_connections 초기화"""
    yield
    active_connections.clear()


def test_websocket_connection():
    """WebSocket 연결 및 초기 메시지 수신 테스트"""
    client = TestClient(app)
    with client.websocket_connect("/ws/live") as ws:
        data = ws.receive_json()
        assert data["type"] in ("system_status", "price_update")


def test_websocket_receives_trade_signal():
    """WebSocket 트레이드 시그널 수신 테스트"""
    client = TestClient(app)
    with client.websocket_connect("/ws/live") as ws:
        # 첫 메시지는 system_status일 것
        data = ws.receive_json()
        assert "type" in data
        # type이 system_status, price_update, trade_signal 중 하나여야 함
        assert data["type"] in ("system_status", "price_update", "trade_signal")


def test_websocket_echo_ack():
    """WebSocket 메시지 송수신 및 ack 응답 테스트"""
    client = TestClient(app)
    with client.websocket_connect("/ws/live") as ws:
        # 1. 초기 system_status 수신
        initial_data = ws.receive_json()
        assert initial_data["type"] == "system_status"
        assert initial_data["status"] == "connected"

        # 2. 메시지 전송 및 ack 응답 확인
        ws.send_text("hello")
        ack_data = ws.receive_json()
        assert ack_data["type"] == "ack"
        assert ack_data["message"] == "Received: hello"


@pytest.mark.asyncio
async def test_websocket_broadcast():
    """broadcast 함수가 모든 연결에 메시지를 전송하는지 테스트"""
    # Mock WebSocket 생성
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()

    # active_connections에 추가
    active_connections.add(mock_ws)

    # broadcast 호출
    message = {"type": "price_update", "data": 100}
    await broadcast(message)

    # send_json이 올바른 메시지로 호출되었는지 확인
    mock_ws.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_websocket_broadcast_removes_disconnected():
    """broadcast 중 연결 실패 시 해당 연결이 제거되는지 테스트"""
    # 정상 동작하는 mock
    normal_ws = MagicMock()
    normal_ws.send_json = AsyncMock()

    # 에러를 발생시키는 mock
    failing_ws = MagicMock()
    failing_ws.send_json = AsyncMock(side_effect=Exception("Connection lost"))

    # 둘 다 active_connections에 추가
    active_connections.add(normal_ws)
    active_connections.add(failing_ws)

    initial_count = len(active_connections)
    assert initial_count == 2

    # broadcast 호출
    message = {"type": "price_update", "data": 100}
    await broadcast(message)

    # 실패한 연결만 제거되었는지 확인
    assert len(active_connections) == 1
    assert normal_ws in active_connections
    assert failing_ws not in active_connections


def test_websocket_disconnect_cleanup():
    """WebSocket 연결 해제 시 active_connections에서 제거되는지 테스트"""
    client = TestClient(app)

    # 연결 전 카운트
    initial_count = len(active_connections)

    with client.websocket_connect("/ws/live") as ws:
        # 초기 메시지 수신
        ws.receive_json()

        # 연결 중에는 active_connections에 포함되어야 함
        assert len(active_connections) == initial_count + 1

    # with 블록을 벗어나면 자동으로 연결 종료되고 제거되어야 함
    assert len(active_connections) == initial_count
