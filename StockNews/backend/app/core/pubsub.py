"""Redis Pub/Sub 속보 발행/구독."""

import json
import logging

logger = logging.getLogger(__name__)

CHANNEL_PREFIX = "news_breaking_"
BREAKING_THRESHOLD = 80.0


def get_channel_name(market: str) -> str:
    """마켓별 Redis 채널명."""
    return f"{CHANNEL_PREFIX}{market.lower()}"


def should_publish_breaking(score: float) -> bool:
    """속보 발행 여부 판단."""
    return score >= BREAKING_THRESHOLD


def publish_breaking_news(
    redis_client,
    stock_code: str,
    title: str,
    score: float,
    market: str,
) -> bool:
    """속보 이벤트를 Redis에 발행."""
    channel = get_channel_name(market)
    payload = json.dumps({
        "type": "breaking_news",
        "stock_code": stock_code,
        "title": title,
        "score": score,
        "market": market,
    }, ensure_ascii=False)

    try:
        redis_client.publish(channel, payload)
        logger.info("Published breaking news to %s: %s", channel, title)
        return True
    except Exception as e:
        logger.error("Failed to publish breaking news: %s", e)
        return False
