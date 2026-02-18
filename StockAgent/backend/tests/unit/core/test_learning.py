"""T-B19: Learning DB / Analyzer 테스트"""

from src.core.learning import LearningAnalyzer


def test_calculate_win_rate():
    """승률 계산"""
    trades = [{"pnl": 1000}, {"pnl": -500}, {"pnl": 2000}]
    result = LearningAnalyzer.calc_win_rate(trades)
    assert abs(result - 66.67) < 0.1


def test_calculate_win_rate_empty():
    """거래 없을 때 승률 0"""
    result = LearningAnalyzer.calc_win_rate([])
    assert result == 0.0


def test_calculate_max_drawdown():
    """최대 낙폭 (MDD) 계산"""
    equity_curve = [100, 110, 95, 105, 90, 100]
    mdd = LearningAnalyzer.calc_max_drawdown(equity_curve)
    assert abs(mdd - 18.18) < 0.1  # (110→90)/110


def test_max_drawdown_monotonic_increase():
    """단조 증가 시 MDD = 0"""
    equity_curve = [100, 110, 120, 130]
    mdd = LearningAnalyzer.calc_max_drawdown(equity_curve)
    assert mdd == 0.0


def test_identify_best_worst_pattern():
    """전략별 최고/최저 패턴 식별"""
    trades = [
        {"strategy_tag": "volume_leader", "pnl": 5000},
        {"strategy_tag": "news_breakout", "pnl": -3000},
        {"strategy_tag": "volume_leader", "pnl": 3000},
    ]
    patterns = LearningAnalyzer.identify_patterns(trades)
    assert patterns["best"] == "volume_leader"
    assert patterns["worst"] == "news_breakout"


def test_identify_patterns_empty():
    """거래 없을 때 패턴 없음"""
    patterns = LearningAnalyzer.identify_patterns([])
    assert patterns["best"] is None
    assert patterns["worst"] is None
