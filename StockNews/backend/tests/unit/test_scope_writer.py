"""scope_writer 모듈 테스트."""
from unittest.mock import patch


class TestReadScopeYaml:
    """read_scope_yaml() 테스트."""

    def test_reads_yaml_from_scope_file(self):
        """기존 scope 파일에서 YAML을 정상적으로 읽는다."""
        # Use the actual scope file
        from app.core.scope_writer import read_scope_yaml
        data = read_scope_yaml()
        assert "korean_market" in data
        assert "us_stocks" in data
        assert "korean_stocks" in data

    def test_returns_empty_dict_when_file_not_found(self):
        """파일 미존재 시 빈 dict 반환."""
        from app.core.scope_writer import read_scope_yaml
        with patch("app.core.scope_writer._find_scope_file", return_value=None):
            result = read_scope_yaml()
            assert result == {}


class TestWriteScopeYaml:
    """write_scope_yaml() 테스트."""

    def test_roundtrip_preserves_data(self, tmp_path):
        """읽기 → 쓰기 → 읽기 라운드트립에서 데이터 보존."""
        # Create a temp scope file
        content = '''---
korean_market:
  search_queries:
    - query: "삼성전자"
      stock_code: "005930"
korean_stocks:
  삼성전자: "005930"
us_stocks:
  AAPL: "Apple"
---

# Documentation Section

This is markdown content that should be preserved.
'''
        scope_file = tmp_path / "docs" / "NewsCollectionScope.md"
        scope_file.parent.mkdir(parents=True, exist_ok=True)
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import _write_lock, read_scope_yaml, write_scope_yaml
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            original = read_scope_yaml()
            with _write_lock:
                write_scope_yaml(original)
            reloaded = read_scope_yaml()

            assert reloaded["korean_market"]["search_queries"][0]["query"] == "삼성전자"
            assert reloaded["korean_stocks"]["삼성전자"] == "005930"
            assert reloaded["us_stocks"]["AAPL"] == "Apple"

    def test_preserves_markdown_below_yaml(self, tmp_path):
        """YAML 아래 Markdown 문서가 보존된다."""
        content = '''---
key: value
---

# Important Documentation

This must be preserved.
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import _write_lock, write_scope_yaml
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            with _write_lock:
                write_scope_yaml({"key": "new_value"})
            result = scope_file.read_text(encoding="utf-8")
            assert "# Important Documentation" in result
            assert "This must be preserved." in result
            assert "new_value" in result


class TestAddKrSearchQuery:
    """add_kr_search_query() 테스트."""

    def test_adds_new_query(self, tmp_path):
        """새 검색 쿼리를 추가한다."""
        content = '''---
korean_market:
  search_queries:
    - query: "삼성전자"
      stock_code: "005930"
---
# Doc
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import add_kr_search_query, read_scope_yaml
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            result = add_kr_search_query("한화에어로스페이스", "012450")
            assert result is True
            data = read_scope_yaml()
            codes = [q["stock_code"] for q in data["korean_market"]["search_queries"]]
            assert "012450" in codes

    def test_ignores_duplicate(self, tmp_path):
        """이미 존재하는 종목코드는 무시한다."""
        content = '''---
korean_market:
  search_queries:
    - query: "삼성전자"
      stock_code: "005930"
---
# Doc
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import add_kr_search_query
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            result = add_kr_search_query("삼성전자", "005930")
            assert result is False


class TestAddKoreanStock:
    """add_korean_stock() 테스트."""

    def test_adds_new_stock(self, tmp_path):
        """새 종목을 사전에 추가한다."""
        content = '''---
korean_stocks:
  삼성전자: "005930"
---
# Doc
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import add_korean_stock, read_scope_yaml
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            result = add_korean_stock("카카오", "035720")
            assert result is True
            data = read_scope_yaml()
            assert "카카오" in data["korean_stocks"]

    def test_ignores_existing_stock(self, tmp_path):
        """이미 존재하는 종목명은 무시한다."""
        content = '''---
korean_stocks:
  삼성전자: "005930"
---
# Doc
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import add_korean_stock
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            result = add_korean_stock("삼성전자", "005930")
            assert result is False


class TestAddUsStock:
    """add_us_stock() 테스트."""

    def test_adds_new_us_stock(self, tmp_path):
        """새 미국 종목을 추가한다."""
        content = '''---
us_stocks:
  AAPL: "Apple"
---
# Doc
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import add_us_stock, read_scope_yaml
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            result = add_us_stock("TSLA", "Tesla")
            assert result is True
            data = read_scope_yaml()
            assert "TSLA" in data["us_stocks"]

    def test_ignores_existing_us_stock(self, tmp_path):
        """이미 존재하는 ticker는 무시한다."""
        content = '''---
us_stocks:
  AAPL: "Apple"
---
# Doc
'''
        scope_file = tmp_path / "scope.md"
        scope_file.write_text(content, encoding="utf-8")

        from app.core.scope_writer import add_us_stock
        with patch("app.core.scope_writer._find_scope_file", return_value=scope_file):
            result = add_us_stock("AAPL", "Apple")
            assert result is False
