"""T-B10: Opening Scanner 단위 테스트"""

import pytest


def test_rank_by_trade_value():
    """거래대금 랭킹"""
    from src.core.scanner import Scanner

    stocks = [
        {"code": "005930", "trade_value": 500_000_000},
        {"code": "000660", "trade_value": 800_000_000},
        {"code": "035720", "trade_value": 300_000_000},
    ]
    ranked = Scanner.rank_by_trade_value(stocks, top_n=2)
    assert len(ranked) == 2
    assert ranked[0]["code"] == "000660"


def test_detect_volume_surge():
    """전일 대비 거래량 급증 감지"""
    from src.core.scanner import Scanner

    result = Scanner.detect_volume_surge(
        today_volume=1_000_000, prev_volume=200_000, threshold=3.0
    )
    assert result is True


def test_calculate_opening_range():
    """장초 Range 계산 (09:00~09:30 고/저)"""
    from src.core.scanner import Scanner

    candles = [
        {"time": "09:00", "high": 71000, "low": 69500},
        {"time": "09:15", "high": 71500, "low": 70000},
        {"time": "09:30", "high": 72000, "low": 70500},
    ]
    range_ = Scanner.calc_opening_range(candles)
    assert range_["high"] == 72000
    assert range_["low"] == 69500


def test_detect_volume_surge_zero_prev_volume():
    """전일 거래량 0일 때 False 반환 (line 39 coverage)"""
    from src.core.scanner import Scanner

    result = Scanner.detect_volume_surge(
        today_volume=1000, prev_volume=0, threshold=3.0
    )
    assert result is False


def test_calc_opening_range_empty():
    """빈 캔들 리스트 입력 시 zeros 반환 (line 54 coverage)"""
    from src.core.scanner import Scanner

    range_ = Scanner.calc_opening_range([])
    assert range_["high"] == 0
    assert range_["low"] == 0
