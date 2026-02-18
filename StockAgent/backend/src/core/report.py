"""자동 리포트 생성기"""

import logging

from src.core.learning import LearningAnalyzer

logger = logging.getLogger("stockagent.core.report")


class ReportGenerator:
    """일간/주간 매매 성과 리포트"""

    @staticmethod
    def daily(date: str, trades: list[dict]) -> dict:
        """일간 리포트 생성"""
        total_trades = len(trades)
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        win_rate = LearningAnalyzer.calc_win_rate(trades)
        patterns = LearningAnalyzer.identify_patterns(trades)

        report = {
            "date": date,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "best_pattern": patterns.get("best"),
            "worst_pattern": patterns.get("worst"),
        }

        logger.info("일간 리포트 생성: %s - %d건, 승률 %.1f%%", date, total_trades, win_rate)
        return report
