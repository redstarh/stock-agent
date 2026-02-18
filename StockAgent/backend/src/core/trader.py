"""B-8 자동매매 루프 프레임워크"""

import logging
from datetime import datetime, time

from src.config import Settings

logger = logging.getLogger("stockagent.core.trader")


class Trader:
    """자동매매 루프 관리자"""

    def __init__(self, config: Settings):
        """
        Args:
            config: 애플리케이션 설정
        """
        self._config = config
        self._is_running = False

        # 장 시간: 09:00 ~ 15:30
        self._market_open = time(9, 0)
        self._market_close = time(15, 30)

        logger.info("Trader 초기화 완료")

    @property
    def is_running(self) -> bool:
        """매매 루프 실행 상태"""
        return self._is_running

    async def start(self) -> None:
        """매매 루프 시작"""
        if self._is_running:
            logger.warning("매매 루프가 이미 실행 중입니다")
            return

        self._is_running = True
        logger.info("매매 루프 시작")

    async def stop(self) -> None:
        """매매 루프 정지"""
        if not self._is_running:
            logger.warning("매매 루프가 실행 중이 아닙니다")
            return

        self._is_running = False
        logger.info("매매 루프 정지")

    async def run_cycle(self) -> dict:
        """
        매매 사이클 1회 실행

        Returns:
            dict: 사이클 실행 결과
                - status: "executed" | "no_signal" | "skipped" | "market_closed"
                - timestamp: 실행 시각
                - message: 상세 메시지 (선택)
        """
        now = self._now()

        # 장 시간 체크
        if not self._is_market_open(now):
            logger.debug("장 외 시간: %s", now)
            return {
                "status": "market_closed",
                "timestamp": now.isoformat(),
                "message": "장 외 시간",
            }

        logger.info("매매 사이클 실행: %s", now)

        # Sprint 4: 기본 골격만 구현
        # Sprint 5: 전략 엔진(B-13) 통합 후 실제 로직 구현
        # 현재는 시세수집 → 주문실행의 프레임워크만 제공

        try:
            # TODO: Sprint 5에서 구현
            # 1. 시세 수집 (MarketDataCollector)
            # 2. 전략 신호 생성 (StrategyEngine)
            # 3. 리스크 체크 (RiskManager)
            # 4. 주문 실행 (KiwoomOrder)

            return {
                "status": "no_signal",
                "timestamp": now.isoformat(),
                "message": "전략 엔진 미구현 (Sprint 5 예정)",
            }

        except Exception as e:
            logger.error("매매 사이클 실행 중 오류: %s", e, exc_info=True)
            return {
                "status": "skipped",
                "timestamp": now.isoformat(),
                "message": f"오류: {e}",
            }

    def _now(self) -> datetime:
        """
        현재 시각 반환 (테스트 가능하도록 메서드로 분리)

        Returns:
            datetime: 현재 시각
        """
        return datetime.now()

    def _is_market_open(self, dt: datetime) -> bool:
        """
        장 시간 여부 확인

        Args:
            dt: 확인할 시각

        Returns:
            bool: 장 시간이면 True, 아니면 False
        """
        # 주말 체크 (월~금만 거래)
        if dt.weekday() >= 5:  # 5=토요일, 6=일요일
            return False

        # 시간 체크 (09:00 ~ 15:30)
        current_time = dt.time()
        return self._market_open <= current_time <= self._market_close
