"""T-B12: Redis 뉴스 구독 테스트"""

import json
import asyncio

import pytest
import fakeredis.aioredis

from src.core.news_subscriber import NewsSubscriber


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis()


@pytest.mark.asyncio
async def test_redis_subscribe(fake_redis):
    """Redis 채널 구독 및 메시지 수신"""
    subscriber = NewsSubscriber(redis=fake_redis)
    received = []

    subscriber.on_breaking_news(lambda msg: received.append(msg))

    # 구독 시작 (백그라운드)
    task = asyncio.create_task(subscriber.subscribe("news_breaking_kr"))

    # 구독 준비 대기
    await asyncio.sleep(0.1)

    # 메시지 발행
    await fake_redis.publish("news_breaking_kr", json.dumps({
        "code": "005930", "headline": "삼성전자 실적 발표", "score": 85
    }))

    await asyncio.sleep(0.1)
    subscriber.stop()
    await task

    assert len(received) == 1
    assert received[0]["score"] == 85
    assert received[0]["code"] == "005930"


@pytest.mark.asyncio
async def test_redis_multiple_messages(fake_redis):
    """여러 메시지 수신"""
    subscriber = NewsSubscriber(redis=fake_redis)
    received = []

    subscriber.on_breaking_news(lambda msg: received.append(msg))

    task = asyncio.create_task(subscriber.subscribe("news_breaking_kr"))
    await asyncio.sleep(0.1)

    for i in range(3):
        await fake_redis.publish("news_breaking_kr", json.dumps({
            "code": f"00{i}", "headline": f"뉴스{i}", "score": 50 + i * 10
        }))

    await asyncio.sleep(0.1)
    subscriber.stop()
    await task

    assert len(received) == 3


@pytest.mark.asyncio
async def test_redis_invalid_json(fake_redis):
    """잘못된 JSON 메시지 무시"""
    subscriber = NewsSubscriber(redis=fake_redis)
    received = []

    subscriber.on_breaking_news(lambda msg: received.append(msg))

    task = asyncio.create_task(subscriber.subscribe("news_breaking_kr"))
    await asyncio.sleep(0.1)

    await fake_redis.publish("news_breaking_kr", "not-json")
    await fake_redis.publish("news_breaking_kr", json.dumps({"code": "005930", "score": 90}))

    await asyncio.sleep(0.1)
    subscriber.stop()
    await task

    assert len(received) == 1
    assert received[0]["score"] == 90
