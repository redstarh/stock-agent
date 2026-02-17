"""RED: 종목 매핑 로직 단위 테스트."""

import pytest


class TestStockMapper:
    def test_exact_name_match(self):
        """'삼성전자' → '005930'."""
        from app.processing.stock_mapper import map_stock_name

        result = map_stock_name("삼성전자")
        assert result == "005930"

    def test_partial_name_match(self):
        """'삼성전자우' → '005935'."""
        from app.processing.stock_mapper import map_stock_name

        result = map_stock_name("삼성전자우")
        assert result == "005935"

    def test_english_name(self):
        """'NAVER' → '035420'."""
        from app.processing.stock_mapper import map_stock_name

        result = map_stock_name("NAVER")
        assert result == "035420"

    def test_unknown_name_returns_none(self):
        """미등록 종목명 → None."""
        from app.processing.stock_mapper import map_stock_name

        result = map_stock_name("존재하지않는회사")
        assert result is None

    def test_multiple_stocks_in_title(self):
        """'삼성전자와 SK하이닉스 실적' → ['005930', '000660']."""
        from app.processing.stock_mapper import extract_stock_codes

        codes = extract_stock_codes("삼성전자와 SK하이닉스 실적 발표")
        assert "005930" in codes
        assert "000660" in codes

    def test_ambiguous_stock_name(self):
        """'삼성' → 다중 매칭 시 가장 대표 종목 반환."""
        from app.processing.stock_mapper import find_matching_stocks

        results = find_matching_stocks("삼성")
        assert len(results) >= 1
        # 삼성전자가 포함되어야 함
        assert any(r["code"] == "005930" for r in results)

    def test_case_insensitive_english(self):
        """'naver' (소문자) → '035420'."""
        from app.processing.stock_mapper import map_stock_name

        result = map_stock_name("naver")
        assert result == "035420"

    def test_stock_dictionary_size(self):
        """종목 사전에 최소 50개 이상 종목 등록."""
        from app.processing.stock_mapper import STOCK_DICT

        assert len(STOCK_DICT) >= 50
