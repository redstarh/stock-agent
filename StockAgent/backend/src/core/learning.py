"""Learning DB: 매매 성과 분석"""

import logging
from collections import defaultdict

logger = logging.getLogger("stockagent.core.learning")


class LearningAnalyzer:
    """매매 성과 통계 및 패턴 분석"""

    @staticmethod
    def calc_win_rate(trades: list[dict]) -> float:
        """승률 계산 (%). 거래 없으면 0."""
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t["pnl"] > 0)
        return round(wins / len(trades) * 100, 2)

    @staticmethod
    def calc_max_drawdown(equity_curve: list[float | int]) -> float:
        """최대 낙폭 (MDD) 계산 (%). 단조 증가 시 0."""
        if len(equity_curve) < 2:
            return 0.0

        peak = equity_curve[0]
        max_dd = 0.0

        for value in equity_curve[1:]:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd

        return round(max_dd, 2)

    @staticmethod
    def identify_patterns(trades: list[dict]) -> dict:
        """전략 태그별 총 수익으로 best/worst 패턴 식별"""
        if not trades:
            return {"best": None, "worst": None}

        pnl_by_tag: dict[str, int] = defaultdict(int)
        for t in trades:
            pnl_by_tag[t["strategy_tag"]] += t["pnl"]

        best = max(pnl_by_tag, key=pnl_by_tag.get)
        worst = min(pnl_by_tag, key=pnl_by_tag.get)

        return {"best": best, "worst": worst}
