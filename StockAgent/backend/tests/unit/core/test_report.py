"""T-B20: 자동 리포트 생성 테스트"""
import pytest
from src.core.report import ReportGenerator


@pytest.fixture
def seed_trades():
    return [
        {"trade_id": "t1", "stock_code": "005930", "pnl": 10000, "strategy_tag": "volume_leader", "date": "2026-01-15"},
        {"trade_id": "t2", "stock_code": "000660", "pnl": -5000, "strategy_tag": "news_breakout", "date": "2026-01-15"},
        {"trade_id": "t3", "stock_code": "035720", "pnl": 8000, "strategy_tag": "volume_leader", "date": "2026-01-15"},
    ]


def test_generate_daily_report(seed_trades):
    """일간 리포트 생성"""
    report = ReportGenerator.daily(date="2026-01-15", trades=seed_trades)
    assert report["date"] == "2026-01-15"
    assert report["total_trades"] == 3
    assert "win_rate" in report
    assert "total_pnl" in report


def test_daily_report_win_rate(seed_trades):
    """승률 정확도"""
    report = ReportGenerator.daily(date="2026-01-15", trades=seed_trades)
    assert abs(report["win_rate"] - 66.67) < 0.1  # 2/3 wins


def test_daily_report_total_pnl(seed_trades):
    """총 손익 계산"""
    report = ReportGenerator.daily(date="2026-01-15", trades=seed_trades)
    assert report["total_pnl"] == 13000  # 10000 - 5000 + 8000


def test_daily_report_patterns(seed_trades):
    """best/worst 패턴"""
    report = ReportGenerator.daily(date="2026-01-15", trades=seed_trades)
    assert report["best_pattern"] == "volume_leader"
    assert report["worst_pattern"] == "news_breakout"


def test_daily_report_empty_trades():
    """빈 거래 리포트"""
    report = ReportGenerator.daily(date="2026-01-15", trades=[])
    assert report["total_trades"] == 0
    assert report["win_rate"] == 0.0
    assert report["total_pnl"] == 0
