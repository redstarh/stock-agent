"""Strategy Engine: 장초 거래대금 + 뉴스 점수 기반 매매 전략"""

import logging
from dataclasses import dataclass
from typing import Literal

logger = logging.getLogger("stockagent.core.strategy")


@dataclass
class Signal:
    """매매 신호"""

    action: Literal["buy", "hold"]
    reason: str


class Strategy:
    """장초 모멘텀 + 뉴스 점수 기반 매수 전략

    매수 조건 (AND):
    1. volume_rank <= config["top_n"] (거래대금 상위 N)
    2. news_score >= config["news_threshold"] (뉴스 점수 충족)
    3. current_price >= vwap (VWAP 이상)
    4. current_price >= opening_high (장초 돌파)
    """

    def __init__(self, config: dict):
        """전략 초기화

        Args:
            config: 전략 파라미터
                - top_n: 거래대금 상위 N개
                - news_threshold: 뉴스 점수 임계값
                - volume_rank_limit: 거래대금 순위 제한
        """
        self.config = config

    def evaluate(
        self,
        volume_rank: int,
        news_score: int,
        current_price: float,
        opening_high: float,
        vwap: float,
    ) -> Signal:
        """매매 신호 판단

        Args:
            volume_rank: 거래대금 순위 (1부터 시작)
            news_score: 뉴스 점수 (0~100)
            current_price: 현재가
            opening_high: 장초 고가 (09:00~09:30)
            vwap: VWAP (거래대금 가중평균가)

        Returns:
            Signal: 매매 신호 (action, reason)
        """
        # 조건 1: 거래대금 순위 확인
        if volume_rank > self.config["top_n"]:
            return Signal(
                action="hold",
                reason=f"거래대금 순위 미달 (순위: {volume_rank}, 기준: {self.config['top_n']})",
            )

        # 조건 2: 뉴스 점수 확인
        if news_score < self.config["news_threshold"]:
            return Signal(
                action="hold",
                reason=f"뉴스 점수 미달 (점수: {news_score}, 기준: {self.config['news_threshold']})",
            )

        # 조건 3: VWAP 이상 확인
        if current_price < vwap:
            return Signal(
                action="hold",
                reason=f"VWAP 하회 (현재가: {current_price}, VWAP: {vwap})",
            )

        # 조건 4: 장초 고가 돌파 확인
        if current_price < opening_high:
            return Signal(
                action="hold",
                reason=f"장초 돌파 실패 (현재가: {current_price}, 장초고가: {opening_high})",
            )

        # 모든 조건 충족
        return Signal(
            action="buy",
            reason=f"매수 조건 충족 (순위: {volume_rank}, 뉴스: {news_score}, 현재가: {current_price})",
        )
