"""통합 테스트: 요약 API 엔드포인트."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestSummaryAPI:
    @pytest.fixture(autouse=True)
    def setup(self, mock_openai_summary):
        self.client = TestClient(app)

    def test_summarize_endpoint(self):
        resp = self.client.post(
            "/api/v1/news/summarize", json={"title": "삼성전자 4분기 실적 사상 최대"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert isinstance(data["summary"], str)

    def test_summarize_with_body(self):
        resp = self.client.post(
            "/api/v1/news/summarize",
            json={"title": "삼성전자 실적 발표", "body": "삼성전자가 4분기 매출 80조원을 기록했다."},
        )
        assert resp.status_code == 200

    def test_summarize_missing_title(self):
        resp = self.client.post("/api/v1/news/summarize", json={})
        assert resp.status_code == 422  # Validation error
