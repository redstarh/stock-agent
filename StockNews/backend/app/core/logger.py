"""로깅 설정 (loguru)."""

import sys

from loguru import logger

from app.core.config import settings

# 기본 로거 설정 제거 후 재구성
logger.remove()

# 콘솔 출력
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# 파일 출력 (일일 롤링)
logger.add(
    "logs/stocknews_{time:YYYY-MM-DD}.log",
    level="INFO",
    rotation="1 day",
    retention="30 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)
