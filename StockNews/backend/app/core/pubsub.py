"""Redis Pub/Sub 속보 발행/구독."""

import json
import logging
from typing import TYPE_CHECKING

from pydantic import ValidationError

from app.core.scope_loader import load_scope
from app.schemas.pubsub import BreakingNewsMessage, Market, validate_message

if TYPE_CHECKING:
    from app.models.news_event import NewsEvent

logger = logging.getLogger(__name__)

# Scope에서 속보 설정 로드
_scope = load_scope()
_breaking_cfg = _scope.get("breaking_news", {})

CHANNEL_PREFIX = _breaking_cfg.get("channel_prefix", "news_breaking_")
BREAKING_THRESHOLD = _breaking_cfg.get("threshold", 80.0)


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
    stock_name: str | None = None,
    theme: str | None = None,
    sentiment_score: float = 0.0,
    published_at: str | None = None,
) -> bool:
    """속보 이벤트를 Redis에 발행.

    Args:
        redis_client: Redis 클라이언트
        stock_code: 종목 코드
        title: 뉴스 제목
        score: 뉴스 점수 (0-100)
        market: 시장 (KR/US)
        stock_name: 종목명 (optional)
        theme: 테마 (optional)
        sentiment_score: 감성 점수 -1.0~1.0 (optional, default 0.0)
        published_at: 발행 시각 ISO format (optional)

    Returns:
        발행 성공 시 True
    """
    channel = get_channel_name(market)

    # Validate payload with Pydantic model
    try:
        message = BreakingNewsMessage(
            stock_code=stock_code,
            stock_name=stock_name,
            title=title,
            theme=theme,
            sentiment=sentiment_score,
            news_score=score,
            market=Market(market),
            published_at=published_at,
        )
        payload = message.model_dump_json()
    except ValidationError as e:
        logger.error("Invalid message schema: %s", e)
        return False

    try:
        redis_client.publish(channel, payload)
        logger.info("Published breaking news to %s: %s", channel, title)
        return True
    except Exception as e:
        logger.error("Failed to publish breaking news: %s", e)
        return False


def publish_news_event(redis_client, news_event: "NewsEvent", score: float) -> bool:
    """NewsEvent 객체로부터 속보 발행.

    Args:
        redis_client: Redis 클라이언트
        news_event: NewsEvent 인스턴스
        score: 계산된 뉴스 점수

    Returns:
        발행 성공 시 True
    """
    if not should_publish_breaking(score):
        return False

    return publish_breaking_news(
        redis_client=redis_client,
        stock_code=news_event.stock_code,
        title=news_event.title,
        score=score,
        market=news_event.market,
        stock_name=news_event.stock_name,
        theme=news_event.theme,
        sentiment_score=news_event.sentiment_score,
        published_at=news_event.published_at.isoformat() if news_event.published_at else None,
    )


async def subscribe_and_broadcast(redis_client, broadcast_callback):
    """Redis 채널 구독 후 WebSocket으로 브로드캐스트.

    Args:
        redis_client: Async Redis 클라이언트
        broadcast_callback: 메시지를 받았을 때 호출할 async 함수
    """
    pubsub = redis_client.pubsub()
    channels = [get_channel_name("KR"), get_channel_name("US")]

    try:
        await pubsub.subscribe(*channels)
        logger.info(f"Subscribed to Redis channels: {channels}")

        # Async listen loop
        async for message in pubsub.listen():
            if message and message["type"] == "message":
                try:
                    raw_data = json.loads(message["data"])
                    validated = validate_message(raw_data)
                    if validated:
                        await broadcast_callback(validated.model_dump())
                    else:
                        logger.warning("Unknown message type: %s", raw_data.get("type"))
                except ValidationError as e:
                    logger.warning("Invalid message schema: %s", e)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from Redis: %s", message["data"])
                except Exception as e:
                    logger.error("Broadcast callback error: %s", e)

    except Exception as e:
        logger.error(f"Redis subscription error: {e}")
    finally:
        await pubsub.close()
