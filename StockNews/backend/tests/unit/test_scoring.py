"""RED: 뉴스 스코어링 엔진 단위 테스트."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest


class TestRecency:
    def test_within_1h_returns_100(self):
        """1시간 이내 뉴스 → Recency 100."""
        from app.scoring.engine import calc_recency

        now = datetime.now(timezone.utc)
        score = calc_recency(now - timedelta(minutes=30), now)
        assert score >= 95

    def test_24h_returns_about_50(self):
        """24시간 경과 → Recency ~50."""
        from app.scoring.engine import calc_recency

        now = datetime.now(timezone.utc)
        score = calc_recency(now - timedelta(hours=24), now)
        assert 30 <= score <= 70

    def test_48h_returns_about_25(self):
        """48시간 경과 → Recency ~25."""
        from app.scoring.engine import calc_recency

        now = datetime.now(timezone.utc)
        score = calc_recency(now - timedelta(hours=48), now)
        assert 10 <= score <= 40

    def test_7d_returns_near_zero(self):
        """7일 경과 → Recency ≈ 0."""
        from app.scoring.engine import calc_recency

        now = datetime.now(timezone.utc)
        score = calc_recency(now - timedelta(days=7), now)
        assert score <= 5

    def test_future_timestamp_clamped(self):
        """미래 시각 → 100으로 클램프."""
        from app.scoring.engine import calc_recency

        now = datetime.now(timezone.utc)
        score = calc_recency(now + timedelta(hours=1), now)
        assert score == 100

    def test_timezone_handling(self):
        """KST/UTC 혼용 시 올바른 시간차 계산."""
        from app.scoring.engine import calc_recency

        ref = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
        kst_time = datetime(2024, 1, 1, 9, 0, tzinfo=ZoneInfo("Asia/Seoul"))
        utc_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        # KST 09:00 == UTC 00:00, 같은 시각
        assert abs(calc_recency(kst_time, ref) - calc_recency(utc_time, ref)) < 1.0


class TestFrequency:
    def test_zero_news_returns_zero(self):
        """뉴스 0건 → Frequency 0."""
        from app.scoring.engine import calc_frequency

        assert calc_frequency(0) == 0

    def test_linear_scaling(self):
        """뉴스 수에 비례하여 점수 증가."""
        from app.scoring.engine import calc_frequency

        assert calc_frequency(5) < calc_frequency(10)

    def test_max_cap_at_100(self):
        """상한 100 초과 불가."""
        from app.scoring.engine import calc_frequency

        assert calc_frequency(1000) == 100


class TestSentimentScore:
    def test_positive_returns_high(self):
        """positive + score 0.8 → 높은 점수."""
        from app.scoring.engine import calc_sentiment_score

        score = calc_sentiment_score("positive", 0.8)
        assert score >= 70

    def test_negative_returns_low(self):
        """negative + score -0.8 → 낮은 점수."""
        from app.scoring.engine import calc_sentiment_score

        score = calc_sentiment_score("negative", -0.8)
        assert score <= 30

    def test_neutral_returns_mid(self):
        """neutral → 중간 점수 (50)."""
        from app.scoring.engine import calc_sentiment_score

        score = calc_sentiment_score("neutral", 0.0)
        assert score == 50


class TestDisclosureBonus:
    def test_disclosure_gives_100(self):
        """is_disclosure=True → 100."""
        from app.scoring.engine import calc_disclosure

        assert calc_disclosure(True) == 100

    def test_no_disclosure_gives_0(self):
        """is_disclosure=False → 0."""
        from app.scoring.engine import calc_disclosure

        assert calc_disclosure(False) == 0


class TestNewsScore:
    def test_weighted_sum(self):
        """최종 점수 = Recency*0.4 + Frequency*0.3 + Sentiment*0.2 + Disclosure*0.1."""
        from app.scoring.engine import calc_news_score

        score = calc_news_score(
            recency=100, frequency=100, sentiment=100, disclosure=100,
        )
        assert score == 100.0

    def test_score_range_0_to_100(self):
        """최종 점수 0-100 범위."""
        from app.scoring.engine import calc_news_score

        score = calc_news_score(recency=50, frequency=50, sentiment=50, disclosure=50)
        assert 0 <= score <= 100

    def test_all_max_returns_100(self):
        """모든 요소 100 → 최종 100."""
        from app.scoring.engine import calc_news_score

        assert calc_news_score(100, 100, 100, 100) == 100

    def test_all_zero_returns_0(self):
        """모든 요소 0 → 최종 0."""
        from app.scoring.engine import calc_news_score

        assert calc_news_score(0, 0, 0, 0) == 0

    def test_disclosure_increases_score(self):
        """공시 포함 시 점수 상승."""
        from app.scoring.engine import calc_news_score

        without = calc_news_score(recency=80, frequency=60, sentiment=70, disclosure=0)
        with_disc = calc_news_score(recency=80, frequency=60, sentiment=70, disclosure=100)
        assert with_disc > without
