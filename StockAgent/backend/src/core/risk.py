"""Risk Management Engine"""

import logging

logger = logging.getLogger("stockagent.core.risk")


class RiskManager:
    """포지션 사이징, 손절, 일일 손실 한도, 비상 청산"""

    def __init__(
        self,
        max_position_pct: float = 0.10,
        total_capital: int = 10_000_000,
        stop_loss_pct: float = 0.03,
        daily_loss_limit: int = 500_000,
        max_positions: int = 5,
    ):
        self.max_position_pct = max_position_pct
        self.total_capital = total_capital
        self.stop_loss_pct = stop_loss_pct
        self.daily_loss_limit = daily_loss_limit
        self.max_positions = max_positions
        self.current_positions: int = 0
        self._daily_loss: int = 0

    def calc_position_size(self, price: int) -> int:
        """종목당 최대 투자금액 기준 매수 가능 수량"""
        max_amount = int(self.total_capital * self.max_position_pct)
        return max_amount // price

    def check_stop_loss(self, entry_price: int, current_price: int) -> str:
        """손절 판단: 현재가가 진입가 대비 stop_loss_pct 이상 하락하면 'sell'"""
        loss_pct = (entry_price - current_price) / entry_price
        if loss_pct >= self.stop_loss_pct:
            logger.warning(
                "손절 신호: entry=%d, current=%d, loss=%.2f%%",
                entry_price, current_price, loss_pct * 100,
            )
            return "sell"
        return "hold"

    def record_loss(self, amount: int) -> None:
        """일일 손실 누적"""
        self._daily_loss += amount

    def can_trade(self) -> bool:
        """일일 손실 한도 초과 여부"""
        return self._daily_loss < self.daily_loss_limit

    def can_open_position(self) -> bool:
        """동시 보유 종목 수 제한 확인"""
        return self.current_positions < self.max_positions

    def reset_daily(self) -> None:
        """일일 손실 초기화 (매일 장 시작 전)"""
        self._daily_loss = 0

    def emergency_liquidate(self, positions: list[dict]) -> list[dict]:
        """비상 전체 청산 신호 생성"""
        logger.critical("비상 전체 청산 실행: %d 종목", len(positions))
        return [
            {"code": p["code"], "qty": p["qty"], "action": "sell_all"}
            for p in positions
        ]
