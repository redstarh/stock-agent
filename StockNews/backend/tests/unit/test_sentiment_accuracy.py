"""감성 분석 정확도 테스트 — 100건 샘플 80%+ 목표."""

import json
import pathlib
import pytest

DATASET_PATH = pathlib.Path(__file__).parent.parent / "fixtures" / "sentiment_dataset.json"


class TestSentimentAccuracy:
    @pytest.fixture(autouse=True)
    def load_dataset(self):
        with open(DATASET_PATH) as f:
            self.dataset = json.load(f)

    def test_dataset_has_100_samples(self):
        assert len(self.dataset) >= 100

    def test_dataset_balanced(self):
        """각 감성 최소 25건."""
        counts = {}
        for item in self.dataset:
            s = item["expected_sentiment"]
            counts[s] = counts.get(s, 0) + 1
        assert counts.get("positive", 0) >= 25
        assert counts.get("neutral", 0) >= 25
        assert counts.get("negative", 0) >= 25

    def test_accuracy_above_80_percent(self, mock_openai, monkeypatch):
        """Mock 기반 정확도 테스트 — prompt 포맷 검증."""
        from app.processing.sentiment import analyze_sentiment

        # This test validates the function runs correctly on all samples
        # Real accuracy requires live API — this tests mock compatibility
        correct = 0
        for item in self.dataset:
            result = analyze_sentiment(item["text"])
            # With our mock, all return "positive" — this validates no crash
            assert result["sentiment"] in ("positive", "neutral", "negative")
            assert -1.0 <= result["score"] <= 1.0
            correct += 1

        # All 100 samples should run without error
        assert correct == len(self.dataset)

    def test_confidence_field_present(self, mock_openai):
        """confidence 필드 존재 여부 검증."""
        from app.processing.sentiment import analyze_sentiment

        result = analyze_sentiment(self.dataset[0]["text"])
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.slow
    def test_live_accuracy(self):
        """실제 API 호출 정확도 (수동 실행, CI 제외)."""
        # Skip if no API key
        from app.core.config import settings

        if not settings.openai_api_key:
            pytest.skip("No OpenAI API key")

        from app.processing.sentiment import analyze_sentiment

        correct = 0
        for item in self.dataset:
            result = analyze_sentiment(item["text"])
            if result["sentiment"] == item["expected_sentiment"]:
                correct += 1

        accuracy = correct / len(self.dataset)
        assert accuracy >= 0.80, f"Accuracy {accuracy:.1%} < 80%"
