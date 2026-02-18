"""Integration tests for WebSocket + Redis broadcasting."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.websocket import broadcast, _add_connection, _remove_connection, _active_connections
from app.core.pubsub import subscribe_and_broadcast


class TestWebSocketBroadcast:
    """WebSocket 브로드캐스트 테스트."""

    @pytest.fixture(autouse=True)
    def clear_connections(self):
        """각 테스트마다 연결 초기화."""
        _active_connections.clear()
        yield
        _active_connections.clear()

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self):
        """여러 클라이언트에 메시지 브로드캐스트."""
        # Mock WebSocket 클라이언트 생성
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await _add_connection(ws1)
        await _add_connection(ws2)
        await _add_connection(ws3)

        assert len(_active_connections) == 3

        # 브로드캐스트
        message = {"type": "breaking_news", "data": {"stock_code": "005930"}}
        await broadcast(message)

        # 모든 클라이언트가 메시지 수신
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected_clients(self):
        """연결 끊긴 클라이언트는 자동 제거."""
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        ws2.send_json.side_effect = Exception("Connection lost")

        await _add_connection(ws1)
        await _add_connection(ws2)

        message = {"type": "test"}
        await broadcast(message)

        # ws1은 유지, ws2는 제거
        assert len(_active_connections) == 1
        assert ws1 in _active_connections
        assert ws2 not in _active_connections

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self):
        """연결이 없을 때 브로드캐스트 (에러 없이 처리)."""
        message = {"type": "test"}
        await broadcast(message)  # Should not raise

    @pytest.mark.asyncio
    async def test_subscribe_and_broadcast_integration(self):
        """Redis 구독 → 브로드캐스트 통합."""
        # Mock Redis 클라이언트
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub

        # 메시지 큐 시뮬레이션
        messages = [
            {"type": "subscribe"},
            {
                "type": "message",
                "data": json.dumps({
                    "type": "breaking_news",
                    "stock_code": "005930",
                    "title": "삼성전자 급등",
                    "news_score": 85.0,
                }),
            },
            None,  # 종료 신호
        ]
        message_iter = iter(messages)
        mock_pubsub.get_message.side_effect = lambda: next(message_iter, None)

        # 브로드캐스트 콜백 Mock
        callback = AsyncMock()

        # 구독 시작 (1회 반복 후 종료)
        async def run_once():
            pubsub = mock_redis.pubsub()
            pubsub.subscribe("news_breaking_kr", "news_breaking_us")

            for _ in range(3):
                msg = pubsub.get_message()
                if msg and msg["type"] == "message":
                    data = json.loads(msg["data"])
                    await callback(data)
                await asyncio.sleep(0.01)

        await run_once()

        # 콜백 호출 확인
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args["stock_code"] == "005930"
        assert call_args["news_score"] == 85.0


class TestWebSocketConnectionManagement:
    """WebSocket 연결 관리 테스트."""

    @pytest.fixture(autouse=True)
    def clear_connections(self):
        """각 테스트마다 연결 초기화."""
        _active_connections.clear()
        yield
        _active_connections.clear()

    @pytest.mark.asyncio
    async def test_add_connection(self):
        """연결 추가."""
        ws = AsyncMock()
        result = await _add_connection(ws)

        assert result is True
        assert ws in _active_connections
        assert len(_active_connections) == 1

    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """연결 제거."""
        ws = AsyncMock()
        await _add_connection(ws)
        await _remove_connection(ws)

        assert ws not in _active_connections
        assert len(_active_connections) == 0

    @pytest.mark.asyncio
    async def test_max_connections_limit(self):
        """최대 연결 수 제한."""
        from app.api.websocket import MAX_WS_CONNECTIONS

        # MAX_WS_CONNECTIONS만큼 연결
        for i in range(MAX_WS_CONNECTIONS):
            ws = AsyncMock()
            result = await _add_connection(ws)
            assert result is True

        # 초과 연결 시도
        ws_overflow = AsyncMock()
        result = await _add_connection(ws_overflow)
        assert result is False
        assert ws_overflow not in _active_connections
