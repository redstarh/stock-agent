"""T-B13: Strategy Engine 단위 테스트"""

import pytest


@pytest.fixture
def test_strategy_config():
    """테스트용 전략 설정"""
    return {
        "top_n": 5,
        "news_threshold": 70,
        "volume_rank_limit": 10,
    }


def test_buy_signal_all_conditions_met(test_strategy_config):
    """모든 매수 조건 충족 → 매수 신호"""
    from src.core.strategy import Strategy

    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3,
        news_score=75,
        current_price=71000,
        opening_high=70500,
        vwap=70800,
    )
    assert signal.action == "buy"
    assert signal.reason is not None


def test_no_signal_low_news_score(test_strategy_config):
    """뉴스 점수 미달 → 신호 없음"""
    from src.core.strategy import Strategy

    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3,
        news_score=30,
        current_price=71000,
        opening_high=70500,
        vwap=70800,
    )
    assert signal.action == "hold"
    assert "뉴스 점수 미달" in signal.reason


def test_no_signal_below_vwap(test_strategy_config):
    """VWAP 하회 → 신호 없음"""
    from src.core.strategy import Strategy

    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3,
        news_score=75,
        current_price=69000,
        opening_high=70500,
        vwap=70800,
    )
    assert signal.action == "hold"
    assert "VWAP 하회" in signal.reason


def test_config_from_dict():
    """딕셔너리로 전략 파라미터 로드"""
    from src.core.strategy import Strategy

    config = {"top_n": 5, "news_threshold": 70, "volume_rank_limit": 10}
    strategy = Strategy(config=config)
    assert strategy.config["top_n"] == 5
    assert strategy.config["news_threshold"] == 70
    assert strategy.config["volume_rank_limit"] == 10


def test_no_signal_below_opening_high(test_strategy_config):
    """장초 돌파 실패 → 신호 없음"""
    from src.core.strategy import Strategy

    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=3,
        news_score=75,
        current_price=70000,
        opening_high=70500,
        vwap=69800,
    )
    assert signal.action == "hold"
    assert "장초 돌파 실패" in signal.reason


def test_no_signal_poor_volume_rank(test_strategy_config):
    """거래대금 순위 미달 → 신호 없음"""
    from src.core.strategy import Strategy

    strategy = Strategy(config=test_strategy_config)
    signal = strategy.evaluate(
        volume_rank=15,
        news_score=75,
        current_price=71000,
        opening_high=70500,
        vwap=70800,
    )
    assert signal.action == "hold"
    assert "거래대금 순위 미달" in signal.reason
