"""동적 종목 선정 엔진 테스트."""
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.collectors.stock_selector import DynamicStockSelector


class TestSelectBaseStocks:
    """전략 1: 시총 상위 종목 선정."""

    def test_returns_top_n_from_scope(self):
        """scope의 search_queries에서 상위 N개를 반환한다."""
        selector = DynamicStockSelector()
        mock_scope = {
            "korean_market": {
                "search_queries": [
                    {"query": f"Stock{i}", "stock_code": f"00{i:04d}"} for i in range(20)
                ]
            }
        }
        with patch("app.collectors.stock_selector.load_scope", return_value=mock_scope):
            result = selector._select_base_stocks()
            assert len(result) == selector.BASE_STOCK_LIMIT
            assert result[0] == ("Stock0", "000000")

    def test_returns_all_when_fewer_than_limit(self):
        """scope에 종목이 limit 미만이면 전부 반환."""
        selector = DynamicStockSelector()
        mock_scope = {
            "korean_market": {
                "search_queries": [
                    {"query": "삼성전자", "stock_code": "005930"},
                ]
            }
        }
        with patch("app.collectors.stock_selector.load_scope", return_value=mock_scope):
            result = selector._select_base_stocks()
            assert len(result) == 1


class TestSelectNewsMomentum:
    """전략 4: 뉴스 모멘텀 종목."""

    def test_returns_stocks_with_high_news_count(self):
        """최근 24h 뉴스 건수가 높은 종목을 반환한다."""
        selector = DynamicStockSelector()

        # Mock the DB session and query
        mock_result = MagicMock()
        mock_result.stock_code = "005930"
        mock_result.stock_name = "삼성전자"

        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_result]

        result = selector._select_news_momentum(mock_db)
        assert len(result) == 1
        assert result[0] == ("삼성전자", "005930")


class TestSelectDartDisclosure:
    """전략 5: DART 공시 종목."""

    def test_returns_stocks_with_recent_disclosure(self):
        """최근 24h 공시 종목을 반환한다."""
        selector = DynamicStockSelector()

        mock_result = MagicMock()
        mock_result.stock_code = "012450"
        mock_result.stock_name = "한화에어로스페이스"

        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_result]

        result = selector._select_dart_disclosure(mock_db)
        assert len(result) == 1
        assert result[0] == ("한화에어로스페이스", "012450")


class TestSelectDailyStocks:
    """종합 선정 테스트."""

    def test_deduplicates_across_strategies(self):
        """여러 전략에서 중복 종목이 제거된다."""
        selector = DynamicStockSelector()

        with patch.object(selector, "_select_base_stocks", return_value=[
            ("삼성전자", "005930"), ("SK하이닉스", "000660"),
        ]), patch.object(selector, "_select_theme_trending", return_value=[
            ("삼성전자", "005930"),  # duplicate
            ("LG에너지솔루션", "373220"),
        ]), patch.object(selector, "_select_volume_anomaly", return_value=[
            ("한화에어로스페이스", "012450"),
        ]), patch.object(selector, "_select_news_momentum", return_value=[
            ("SK하이닉스", "000660"),  # duplicate
        ]), patch.object(selector, "_select_dart_disclosure", return_value=[
            ("크래프톤", "259960"),
        ]):
            mock_db = MagicMock(spec=Session)
            result = selector.select_daily_stocks(mock_db)

            codes = [code for _, code in result]
            assert len(codes) == len(set(codes))  # No duplicates
            assert len(result) == 5  # 삼성전자, SK하이닉스, LG에너지솔루션, 한화에어로스페이스, 크래프톤
            assert "005930" in codes  # 삼성전자
            assert "000660" in codes  # SK하이닉스
            assert "373220" in codes  # LG에너지솔루션
            assert "012450" in codes  # 한화에어로스페이스
            assert "259960" in codes  # 크래프톤

    def test_respects_max_total_cap(self):
        """MAX_TOTAL_QUERIES 캡이 적용된다."""
        selector = DynamicStockSelector()
        selector.MAX_TOTAL_QUERIES = 3

        with patch.object(selector, "_select_base_stocks", return_value=[
            ("Stock1", "001"), ("Stock2", "002"), ("Stock3", "003"), ("Stock4", "004"),
        ]), patch.object(selector, "_select_theme_trending", return_value=[]), \
             patch.object(selector, "_select_volume_anomaly", return_value=[]), \
             patch.object(selector, "_select_news_momentum", return_value=[]), \
             patch.object(selector, "_select_dart_disclosure", return_value=[]):
            mock_db = MagicMock(spec=Session)
            result = selector.select_daily_stocks(mock_db)
            assert len(result) <= 3
