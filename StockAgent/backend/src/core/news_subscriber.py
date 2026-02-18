"""Redis 뉴스 구독 클라이언트"""

import json
import logging
from typing import Callable

import redis.asyncio as redis

logger = logging.getLogger("stockagent.core.news_subscriber")


class NewsSubscriber:
    """Redis pub/sub으로 속보 뉴스 수신"""

    def __init__(self, redis: redis.Redis):
        self._redis = redis
        self._callbacks: list[Callable] = []
        self._running = False

    def on_breaking_news(self, callback: Callable) -> None:
        """뉴스 수신 콜백 등록"""
        self._callbacks.append(callback)

    async def subscribe(self, channel: str) -> None:
        """채널 구독 시작 (blocking loop)"""
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(channel)
        self._running = True
        logger.info("Redis 채널 구독 시작: %s", channel)

        try:
            while self._running:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=0.1
                )
                if message and message["type"] == "message":
                    await self._handle_message(message["data"])
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    def stop(self) -> None:
        """구독 중단"""
        self._running = False

    async def _handle_message(self, data: bytes | str) -> None:
        """메시지 파싱 및 콜백 호출"""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            payload = json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("잘못된 메시지 무시: %s", e)
            return

        for callback in self._callbacks:
            try:
                callback(payload)
            except Exception as e:
                logger.error("콜백 실행 실패: %s", e)
