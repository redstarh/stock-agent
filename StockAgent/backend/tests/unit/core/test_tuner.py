"""B-21: Parameter Tuning 테스트"""

import pytest
from src.core.tuner import ParameterTuner


def test_optimize_parameters():
    """파라미터 최적화 실행"""
    tuner = ParameterTuner(
        trades=[
            {"strategy_tag": "vol", "pnl": 5000, "volume_rank": 3, "news_score": 80},
            {"strategy_tag": "vol", "pnl": -2000, "volume_rank": 8, "news_score": 60},
            {"strategy_tag": "vol", "pnl": 3000, "volume_rank": 2, "news_score": 90},
        ],
        current_config={"top_n": 5, "news_threshold": 70}
    )
    result = tuner.optimize()
    assert "top_n" in result
    assert "news_threshold" in result


def test_suggest_top_n():
    """거래대금 순위 기준 최적화"""
    tuner = ParameterTuner(
        trades=[
            {"pnl": 5000, "volume_rank": 2},
            {"pnl": -2000, "volume_rank": 8},
            {"pnl": 3000, "volume_rank": 3},
            {"pnl": -1000, "volume_rank": 7},
        ],
        current_config={"top_n": 5, "news_threshold": 70}
    )
    suggested = tuner._suggest_top_n()
    assert 1 <= suggested <= 20


def test_suggest_news_threshold():
    """뉴스 점수 임계값 최적화"""
    tuner = ParameterTuner(
        trades=[
            {"pnl": 5000, "news_score": 80},
            {"pnl": -2000, "news_score": 50},
            {"pnl": 3000, "news_score": 90},
        ],
        current_config={"top_n": 5, "news_threshold": 70}
    )
    suggested = tuner._suggest_news_threshold()
    assert 0 <= suggested <= 100


def test_empty_trades_returns_current():
    """거래 데이터 없으면 현재 설정 반환"""
    tuner = ParameterTuner(
        trades=[],
        current_config={"top_n": 5, "news_threshold": 70}
    )
    result = tuner.optimize()
    assert result == {"top_n": 5, "news_threshold": 70}
