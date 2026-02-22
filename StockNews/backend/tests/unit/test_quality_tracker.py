"""QualityTracker 단위 테스트."""

import threading
from datetime import UTC, datetime

import pytest

from app.collectors.quality_tracker import ItemResult, QualityTracker


def _make_result(
    source: str = "naver",
    market: str = "KR",
    scrape_ok: bool = True,
    llm_confidence: float = 0.8,
    sentiment: str = "positive",
    news_score: float = 70.0,
) -> ItemResult:
    return ItemResult(
        source=source,
        market=market,
        scrape_ok=scrape_ok,
        llm_confidence=llm_confidence,
        sentiment=sentiment,
        news_score=news_score,
        timestamp=datetime.now(UTC),
    )


class TestQualityTracker:
    """QualityTracker 핵심 기능 테스트."""

    def test_record_and_get_stats(self):
        """기록 후 통계 조회."""
        t = QualityTracker()
        t.record(_make_result(source="naver", news_score=75.0, llm_confidence=0.9))
        t.record(_make_result(source="naver", news_score=50.0, llm_confidence=0.7))

        stats = t.get_source_stats("naver")
        assert stats["total_items"] == 2
        assert stats["avg_news_score"] == 62.5
        assert stats["avg_confidence"] == 0.8
        assert stats["last_updated"] is not None

    def test_rolling_window_eviction(self):
        """window_size 초과 시 오래된 항목 제거."""
        t = QualityTracker(window_size=3)
        for i in range(5):
            t.record(_make_result(source="rss", news_score=float(i * 10)))

        stats = t.get_source_stats("rss")
        assert stats["total_items"] == 3
        # Only items with scores 20, 30, 40 remain
        assert stats["avg_news_score"] == 30.0

    def test_empty_source_stats(self):
        """기록 없는 소스 조회."""
        t = QualityTracker()
        stats = t.get_source_stats("unknown")
        assert stats["total_items"] == 0
        assert stats["scrape_success_rate"] == 0.0
        assert stats["last_updated"] is None

    def test_scrape_success_rate(self):
        """성공/실패 비율 정확성."""
        t = QualityTracker()
        t.record(_make_result(source="finnhub", scrape_ok=True))
        t.record(_make_result(source="finnhub", scrape_ok=True))
        t.record(_make_result(source="finnhub", scrape_ok=False))

        stats = t.get_source_stats("finnhub")
        assert abs(stats["scrape_success_rate"] - 2 / 3) < 0.001

    def test_neutral_ratio(self):
        """neutral 감성 비율 계산."""
        t = QualityTracker()
        t.record(_make_result(source="dart", sentiment="positive"))
        t.record(_make_result(source="dart", sentiment="neutral"))
        t.record(_make_result(source="dart", sentiment="neutral"))
        t.record(_make_result(source="dart", sentiment="negative"))

        stats = t.get_source_stats("dart")
        assert stats["neutral_ratio"] == 0.5

    def test_high_score_ratio(self):
        """score >= 60 비율."""
        t = QualityTracker()
        t.record(_make_result(source="naver", news_score=70.0))
        t.record(_make_result(source="naver", news_score=60.0))  # exactly 60 = high
        t.record(_make_result(source="naver", news_score=59.9))
        t.record(_make_result(source="naver", news_score=30.0))

        stats = t.get_source_stats("naver")
        assert stats["high_score_ratio"] == 0.5

    def test_thread_safety(self):
        """멀티스레드 동시 기록."""
        t = QualityTracker()
        errors = []

        def writer(source: str, count: int):
            try:
                for _ in range(count):
                    t.record(_make_result(source=source))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer, args=(f"src_{i}", 50))
            for i in range(4)
        ]
        for th in threads:
            th.start()
        for th in threads:
            th.join()

        assert not errors
        all_stats = t.get_all_stats()
        assert len(all_stats) == 4
        for stats in all_stats.values():
            assert stats["total_items"] == 50

    def test_get_all_stats(self):
        """여러 소스 통계 일괄 조회."""
        t = QualityTracker()
        t.record(_make_result(source="naver"))
        t.record(_make_result(source="rss"))
        t.record(_make_result(source="finnhub"))

        all_stats = t.get_all_stats()
        assert set(all_stats.keys()) == {"naver", "rss", "finnhub"}
        for stats in all_stats.values():
            assert stats["total_items"] == 1

    def test_get_summary(self):
        """전체 요약 계산."""
        t = QualityTracker()
        # naver: 2 items, all scrape_ok, confidence 0.8
        t.record(_make_result(source="naver", scrape_ok=True, llm_confidence=0.8))
        t.record(_make_result(source="naver", scrape_ok=True, llm_confidence=0.8))
        # rss: 1 item, scrape failed, confidence 0.4
        t.record(_make_result(source="rss", scrape_ok=False, llm_confidence=0.4))

        summary = t.get_summary()
        assert summary["total_sources"] == 2
        assert summary["total_items_tracked"] == 3
        # Weighted scrape rate: (1.0*2 + 0.0*1) / 3 = 0.6667
        assert abs(summary["overall_scrape_success_rate"] - 2 / 3) < 0.001
        # Weighted confidence: (0.8*2 + 0.4*1) / 3 = 0.6667
        assert abs(summary["overall_avg_confidence"] - 2 / 3) < 0.001
