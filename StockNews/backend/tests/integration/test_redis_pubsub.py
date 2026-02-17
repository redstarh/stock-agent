"""RED: Redis Pub/Sub 통합 테스트."""

import json

import pytest
import fakeredis


@pytest.fixture
def fake_redis_client():
    """fakeredis 인스턴스."""
    return fakeredis.FakeRedis(decode_responses=True)


class TestRedisPubSub:
    def test_publish_breaking_news(self, fake_redis_client):
        """속보 이벤트 Redis 발행 확인."""
        from app.core.pubsub import publish_breaking_news

        result = publish_breaking_news(
            fake_redis_client,
            stock_code="005930",
            title="삼성전자 속보",
            score=90.0,
            market="KR",
        )
        assert result is True

    def test_subscribe_receives_event(self, fake_redis_client):
        """구독자가 이벤트 수신."""
        from app.core.pubsub import publish_breaking_news, CHANNEL_PREFIX

        pubsub = fake_redis_client.pubsub()
        pubsub.subscribe(f"{CHANNEL_PREFIX}kr")

        # 구독 확인 메시지 소비
        pubsub.get_message()

        publish_breaking_news(
            fake_redis_client,
            stock_code="005930",
            title="삼성전자 속보",
            score=90.0,
            market="KR",
        )

        msg = pubsub.get_message()
        assert msg is not None
        assert msg["type"] == "message"
        data = json.loads(msg["data"])
        assert data["stock_code"] == "005930"

    def test_breaking_threshold_below(self, fake_redis_client):
        """score < 80 → 이벤트 미발행."""
        from app.core.pubsub import should_publish_breaking

        assert should_publish_breaking(score=70.0) is False

    def test_above_threshold_publishes(self, fake_redis_client):
        """score >= 80 → 이벤트 발행 가능."""
        from app.core.pubsub import should_publish_breaking

        assert should_publish_breaking(score=80.0) is True
        assert should_publish_breaking(score=95.0) is True

    def test_channel_name_by_market(self):
        """KR → news_breaking_kr, US → news_breaking_us."""
        from app.core.pubsub import get_channel_name

        assert get_channel_name("KR") == "news_breaking_kr"
        assert get_channel_name("US") == "news_breaking_us"
