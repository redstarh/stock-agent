"""
Unit Test 예제
"""
import pytest
from decimal import Decimal


# ==================== 예제 1: 간단한 계산 함수 테스트 ====================

def calculate_roi(cost: Decimal, current_value: Decimal) -> Decimal:
    """ROI 계산"""
    return ((current_value - cost) / cost) * 100


class TestCalculateROI:
    """ROI 계산 테스트"""

    def test_positive_roi(self):
        """양수 수익률"""
        cost = Decimal("1000")
        current_value = Decimal("1200")

        roi = calculate_roi(cost, current_value)

        assert roi == Decimal("20")

    def test_negative_roi(self):
        """음수 수익률"""
        cost = Decimal("1000")
        current_value = Decimal("800")

        roi = calculate_roi(cost, current_value)

        assert roi == Decimal("-20")

    def test_zero_roi(self):
        """제로 수익률"""
        cost = Decimal("1000")
        current_value = Decimal("1000")

        roi = calculate_roi(cost, current_value)

        assert roi == Decimal("0")

    @pytest.mark.parametrize("cost,current_value,expected", [
        (Decimal("100"), Decimal("120"), Decimal("20")),
        (Decimal("100"), Decimal("80"), Decimal("-20")),
        (Decimal("1000"), Decimal("1500"), Decimal("50")),
    ])
    def test_roi_parametrized(self, cost, current_value, expected):
        """파라미터화된 ROI 테스트"""
        roi = calculate_roi(cost, current_value)
        assert roi == expected


# ==================== 예제 2: 클래스 메서드 테스트 ====================

class Order:
    """주문 클래스 (예제)"""

    def __init__(self, symbol: str, quantity: int, price: Decimal):
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.status = "pending"

    def calculate_total(self) -> Decimal:
        """주문 총액 계산"""
        return self.quantity * self.price

    def mark_as_filled(self):
        """체결 처리"""
        if self.status != "pending":
            raise ValueError("Only pending orders can be filled")
        self.status = "filled"


class TestOrder:
    """주문 클래스 테스트"""

    def test_create_order(self):
        """주문 생성"""
        order = Order("AAPL", 10, Decimal("150"))

        assert order.symbol == "AAPL"
        assert order.quantity == 10
        assert order.status == "pending"

    def test_calculate_total(self):
        """총액 계산"""
        order = Order("AAPL", 10, Decimal("150.00"))

        total = order.calculate_total()

        assert total == Decimal("1500.00")

    def test_mark_as_filled(self):
        """체결 처리"""
        order = Order("AAPL", 10, Decimal("150"))

        order.mark_as_filled()

        assert order.status == "filled"

    def test_mark_as_filled_raises_error_when_already_filled(self):
        """이미 체결된 주문은 다시 체결 불가"""
        order = Order("AAPL", 10, Decimal("150"))
        order.mark_as_filled()

        with pytest.raises(ValueError, match="Only pending orders"):
            order.mark_as_filled()


# ==================== 예제 3: Mock 사용 ====================

from unittest.mock import Mock, patch


class PortfolioService:
    """포트폴리오 서비스 (예제)"""

    def __init__(self, market_data_service):
        self.market_data_service = market_data_service

    def get_position_value(self, symbol: str, quantity: int) -> Decimal:
        """포지션 평가액"""
        current_price = self.market_data_service.get_price(symbol)
        return Decimal(quantity) * current_price


class TestPortfolioServiceWithMock:
    """Mock을 사용한 테스트"""

    def test_get_position_value(self):
        """포지션 평가액 계산 (Mock 사용)"""
        # Mock 생성
        mock_market_data = Mock()
        mock_market_data.get_price.return_value = Decimal("160")

        service = PortfolioService(mock_market_data)

        # 테스트 실행
        value = service.get_position_value("AAPL", 10)

        # 검증
        assert value == Decimal("1600")
        mock_market_data.get_price.assert_called_once_with("AAPL")

    @patch('__main__.PortfolioService')
    def test_with_patch_decorator(self, mock_service):
        """@patch 데코레이터 사용"""
        mock_service.get_position_value.return_value = Decimal("1600")

        # 테스트 로직...


# ==================== 예제 4: Fixture 사용 ====================

@pytest.fixture
def sample_order():
    """샘플 주문 픽스처"""
    return Order("AAPL", 10, Decimal("150"))


class TestWithFixture:
    """Fixture를 사용한 테스트"""

    def test_using_fixture(self, sample_order):
        """Fixture 사용"""
        assert sample_order.symbol == "AAPL"
        assert sample_order.calculate_total() == Decimal("1500")

    def test_modify_fixture(self, sample_order):
        """Fixture 수정 (각 테스트마다 독립적)"""
        sample_order.mark_as_filled()
        assert sample_order.status == "filled"


# ==================== 실행 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
