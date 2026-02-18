"""Parameter Tuning: 과거 매매 성과 기반 파라미터 최적화"""

import logging
import statistics

logger = logging.getLogger("stockagent.core.tuner")


class ParameterTuner:
    """매매 전략 파라미터 자동 튜닝

    과거 매매 데이터 분석하여 수익성 높은 파라미터 조합 제안:
    - top_n: 거래대금 상위 N개 (volume_rank 기반)
    - news_threshold: 뉴스 점수 임계값 (news_score 기반)
    """

    def __init__(self, trades: list[dict], current_config: dict):
        """초기화

        Args:
            trades: 과거 매매 데이터 [{"pnl", "volume_rank", "news_score", ...}, ...]
            current_config: 현재 전략 설정 {"top_n", "news_threshold"}
        """
        self.trades = trades
        self.current_config = current_config

    def optimize(self) -> dict:
        """최적 파라미터 제안

        Returns:
            dict: {"top_n": int, "news_threshold": int}
        """
        if not self.trades:
            logger.info("거래 데이터 없음 - 현재 설정 유지")
            return self.current_config

        suggested_config = {
            "top_n": self._suggest_top_n(),
            "news_threshold": self._suggest_news_threshold(),
        }

        logger.info(f"파라미터 최적화: {self.current_config} → {suggested_config}")
        return suggested_config

    def _suggest_top_n(self) -> int:
        """거래대금 순위 기준 최적화

        수익 거래(pnl > 0)의 volume_rank 중앙값으로 top_n 제안
        수익 거래 없으면 현재 설정 유지

        Returns:
            int: 제안 top_n (1~20 범위로 제한)
        """
        winning_trades = [t for t in self.trades if t["pnl"] > 0]

        if not winning_trades:
            logger.warning("수익 거래 없음 - top_n 유지")
            return self.current_config["top_n"]

        # volume_rank 필드 있는 거래만 필터링
        ranks = [t["volume_rank"] for t in winning_trades if "volume_rank" in t]

        if not ranks:
            logger.warning("volume_rank 데이터 없음 - top_n 유지")
            return self.current_config["top_n"]

        median_rank = int(statistics.median(ranks))
        suggested = min(max(median_rank, 1), 20)  # 1~20 범위 제한

        logger.info(f"top_n 제안: {suggested} (수익 거래 순위 중앙값: {median_rank})")
        return suggested

    def _suggest_news_threshold(self) -> int:
        """뉴스 점수 임계값 최적화

        수익 거래(pnl > 0)의 news_score 중 하위 25% 백분위수를 임계값으로 제안
        (수익 거래 중 낮은 점수까지 포함하되, 너무 낮지 않게)

        Returns:
            int: 제안 news_threshold (0~100 범위로 제한)
        """
        winning_trades = [t for t in self.trades if t["pnl"] > 0]

        if not winning_trades:
            logger.warning("수익 거래 없음 - news_threshold 유지")
            return self.current_config["news_threshold"]

        # news_score 필드 있는 거래만 필터링
        scores = [t["news_score"] for t in winning_trades if "news_score" in t]

        if not scores:
            logger.warning("news_score 데이터 없음 - news_threshold 유지")
            return self.current_config["news_threshold"]

        # 하위 25% 백분위수 사용 (수익 거래 중 낮은 점수 기준)
        threshold = int(statistics.quantiles(scores, n=4)[0])  # 0번째가 25%
        suggested = min(max(threshold, 0), 100)  # 0~100 범위 제한

        logger.info(f"news_threshold 제안: {suggested} (수익 거래 점수 25% 백분위)")
        return suggested
