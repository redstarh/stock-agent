"""소스별 파이프라인 품질 메트릭 트래커 (인메모리 rolling window)."""

import threading
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ItemResult:
    """단일 파이프라인 처리 결과."""
    source: str
    market: str
    scrape_ok: bool
    llm_confidence: float    # 0.0~1.0
    sentiment: str           # positive/negative/neutral
    news_score: float        # 0~100
    timestamp: datetime


class QualityTracker:
    """소스별 파이프라인 품질 메트릭 (인메모리 rolling window).

    Each source keeps the most recent `_window_size` ItemResults.
    Thread-safe via threading.Lock (pipeline uses asyncio.to_thread).
    """

    def __init__(self, window_size: int = 100):
        self._window_size = window_size
        self._results: dict[str, deque[ItemResult]] = {}
        self._lock = threading.Lock()

    def record(self, result: ItemResult) -> None:
        """Record a pipeline result for a source."""
        with self._lock:
            if result.source not in self._results:
                self._results[result.source] = deque(maxlen=self._window_size)
            self._results[result.source].append(result)

    def get_source_stats(self, source: str) -> dict:
        """Get quality stats for a single source."""
        with self._lock:
            items = list(self._results.get(source, []))

        if not items:
            return {
                "total_items": 0,
                "scrape_success_rate": 0.0,
                "avg_confidence": 0.0,
                "neutral_ratio": 0.0,
                "avg_news_score": 0.0,
                "high_score_ratio": 0.0,
                "last_updated": None,
            }

        total = len(items)
        scrape_ok_count = sum(1 for i in items if i.scrape_ok)
        neutral_count = sum(1 for i in items if i.sentiment == "neutral")
        high_score_count = sum(1 for i in items if i.news_score >= 60)

        return {
            "total_items": total,
            "scrape_success_rate": round(scrape_ok_count / total, 4),
            "avg_confidence": round(sum(i.llm_confidence for i in items) / total, 4),
            "neutral_ratio": round(neutral_count / total, 4),
            "avg_news_score": round(sum(i.news_score for i in items) / total, 2),
            "high_score_ratio": round(high_score_count / total, 4),
            "last_updated": items[-1].timestamp.isoformat(),
        }

    def get_all_stats(self) -> dict[str, dict]:
        """Get quality stats for all sources."""
        with self._lock:
            sources = list(self._results.keys())
        return {source: self.get_source_stats(source) for source in sources}

    def get_summary(self) -> dict:
        """Get overall summary across all sources."""
        all_stats = self.get_all_stats()
        if not all_stats:
            return {
                "total_sources": 0,
                "total_items_tracked": 0,
                "overall_scrape_success_rate": 0.0,
                "overall_avg_confidence": 0.0,
            }

        total_items = sum(s["total_items"] for s in all_stats.values())
        if total_items == 0:
            return {
                "total_sources": len(all_stats),
                "total_items_tracked": 0,
                "overall_scrape_success_rate": 0.0,
                "overall_avg_confidence": 0.0,
            }

        # Weighted averages by item count
        weighted_scrape = sum(
            s["scrape_success_rate"] * s["total_items"] for s in all_stats.values()
        )
        weighted_confidence = sum(
            s["avg_confidence"] * s["total_items"] for s in all_stats.values()
        )

        return {
            "total_sources": len(all_stats),
            "total_items_tracked": total_items,
            "overall_scrape_success_rate": round(weighted_scrape / total_items, 4),
            "overall_avg_confidence": round(weighted_confidence / total_items, 4),
        }


# Module-level singleton
tracker = QualityTracker()
