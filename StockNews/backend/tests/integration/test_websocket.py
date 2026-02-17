"""RED: WebSocket 통합 테스트."""

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.testclient import TestClient

from app.main import app


class TestWebSocket:
    def test_connect(self):
        """WS /ws/news 연결 성공."""
        client = TestClient(app)
        with client.websocket_connect("/ws/news") as ws:
            # 연결 성공 시 welcome 메시지 수신
            data = ws.receive_json()
            assert data["type"] == "connected"

    def test_message_format(self):
        """메시지 type + data 구조 확인."""
        client = TestClient(app)
        with client.websocket_connect("/ws/news") as ws:
            data = ws.receive_json()
            assert "type" in data
            assert isinstance(data["type"], str)

    def test_ping_pong(self):
        """클라이언트 ping → 서버 pong 응답."""
        client = TestClient(app)
        with client.websocket_connect("/ws/news") as ws:
            # welcome 메시지 소비
            ws.receive_json()

            # ping 전송
            ws.send_json({"type": "ping"})
            resp = ws.receive_json()
            assert resp["type"] == "pong"

    def test_max_connections_setting(self):
        """MAX_WS_CONNECTIONS 설정값 확인."""
        from app.api.websocket import MAX_WS_CONNECTIONS

        assert MAX_WS_CONNECTIONS >= 1
        assert isinstance(MAX_WS_CONNECTIONS, int)
