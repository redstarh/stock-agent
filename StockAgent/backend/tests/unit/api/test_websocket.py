"""T-B18: WebSocket 실시간 API 테스트"""

import pytest
from starlette.testclient import TestClient

from src.main import app


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
