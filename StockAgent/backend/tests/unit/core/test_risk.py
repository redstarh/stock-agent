"""T-B14: Risk Management 테스트"""

from src.core.risk import RiskManager


def test_position_size_within_limit():
    """종목당 비중 10% 이하"""
    risk = RiskManager(max_position_pct=0.10, total_capital=10_000_000)
    size = risk.calc_position_size(price=70000)
    assert size * 70000 <= 1_000_000


def test_stop_loss_triggered():
    """손절 가격 도달 시 청산 신호"""
    risk = RiskManager(stop_loss_pct=0.03)
    signal = risk.check_stop_loss(entry_price=70000, current_price=67800)
    assert signal == "sell"


def test_stop_loss_not_triggered():
    """손절 미도달 시 hold"""
    risk = RiskManager(stop_loss_pct=0.03)
    signal = risk.check_stop_loss(entry_price=70000, current_price=68500)
    assert signal == "hold"


def test_daily_loss_limit():
    """1일 최대 손실 초과 시 매매 중단"""
    risk = RiskManager(daily_loss_limit=500_000)
    risk.record_loss(300_000)
    assert risk.can_trade() is True
    risk.record_loss(250_000)
    assert risk.can_trade() is False


def test_max_concurrent_positions():
    """동시 보유 종목 수 제한"""
    risk = RiskManager(max_positions=5)
    risk.current_positions = 5
    assert risk.can_open_position() is False


def test_can_open_position_under_limit():
    """종목 수 미만이면 진입 가능"""
    risk = RiskManager(max_positions=5)
    risk.current_positions = 3
    assert risk.can_open_position() is True


def test_emergency_liquidation():
    """비상 전체 청산"""
    risk = RiskManager()
    signals = risk.emergency_liquidate(positions=[
        {"code": "005930", "qty": 10},
        {"code": "000660", "qty": 5},
    ])
    assert len(signals) == 2
    assert all(s["action"] == "sell_all" for s in signals)
