"""RED: 테마 분류 로직 단위 테스트."""

import pytest


class TestThemeClassifier:
    def test_ai_theme_detection(self):
        """'AI 반도체 수요 증가' → 'AI' 또는 '반도체' 포함."""
        from app.processing.theme_classifier import classify_theme

        themes = classify_theme("AI 반도체 수요 증가로 엔비디아 주가 급등")
        assert "AI" in themes or "반도체" in themes

    def test_battery_theme(self):
        """'2차전지 양극재' → '2차전지' 포함."""
        from app.processing.theme_classifier import classify_theme

        themes = classify_theme("2차전지 양극재 시장 확대 전망")
        assert "2차전지" in themes

    def test_no_theme(self):
        """테마 키워드 없는 텍스트 → 빈 리스트."""
        from app.processing.theme_classifier import classify_theme

        themes = classify_theme("오늘 날씨가 좋습니다")
        assert themes == []

    def test_multiple_themes(self):
        """'AI 기반 바이오 신약' → 2개 이상 테마."""
        from app.processing.theme_classifier import classify_theme

        themes = classify_theme("AI 기반 바이오 신약 개발 가속화")
        assert len(themes) >= 2

    def test_theme_dictionary_has_entries(self):
        """테마 사전에 최소 10개 테마 등록."""
        from app.processing.theme_classifier import THEME_KEYWORDS

        assert len(THEME_KEYWORDS) >= 10
