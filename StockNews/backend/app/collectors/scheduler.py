"""APScheduler 기반 뉴스 수집 스케줄러."""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.core.scope_loader import load_scope, register_reload_callback

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_MINUTES = 1

# 기본값 (scope 파일 미존재 시 fallback)
_DEFAULT_KR_SEARCH_QUERIES = [
    ("삼성전자", "005930"),
    ("SK하이닉스", "000660"),
    ("현대차", "005380"),
    ("NAVER", "035420"),
    ("카카오", "035720"),
    ("LG에너지솔루션", "373220"),
    ("셀트리온", "068270"),
    ("삼성바이오로직스", "207940"),
    ("기아", "000270"),
    ("POSCO홀딩스", "005490"),
]


def _load_kr_search_queries() -> list[tuple[str, str]]:
    """Scope 파일에서 검색 쿼리 로드. 실패 시 기본값 사용."""
    scope = load_scope()
    queries = scope.get("korean_market", {}).get("search_queries", [])
    if queries:
        return [(q["query"], q["stock_code"]) for q in queries]
    return _DEFAULT_KR_SEARCH_QUERIES


_kr_search_queries: list[tuple[str, str]] = _load_kr_search_queries()


def get_kr_search_queries() -> list[tuple[str, str]]:
    """현재 KR 검색 쿼리 목록 반환."""
    return _kr_search_queries


def _on_scope_reload(data: dict) -> None:
    """Scope 리로드 시 검색 쿼리 갱신."""
    global _kr_search_queries
    queries = data.get("korean_market", {}).get("search_queries", [])
    if queries:
        _kr_search_queries = [(q["query"], q["stock_code"]) for q in queries]
        logger.info("KR search queries updated: %d queries", len(_kr_search_queries))


register_reload_callback(_on_scope_reload)


def _collect_kr_news_job():
    """한국 뉴스 통합 수집 작업 (Naver + RSS 병합 후 단일 파이프라인).

    여러 수집기 결과를 병합하여 교차 수집기 URL/제목 중복을 제거합니다.
    """
    import time

    from app.core.scheduler_state import record_job_run

    logger.info("Korean news collection started (merged)")
    start = time.time()

    async def _run():
        from app.collectors.naver import NaverCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        all_items: list[dict] = []

        # 1. Naver 수집
        naver = NaverCollector()
        for query, stock_code in get_kr_search_queries():
            try:
                items = await naver.collect(query=query, stock_code=stock_code, market="KR")
                all_items.extend(items)
            except Exception as e:
                logger.warning("Naver collect failed for %s: %s", query, e)

        # 2. KR RSS 수집 (설정된 경우)
        feeds = _load_rss_feeds("korean")
        if feeds:
            from app.collectors.rss import RssCollector

            rss = RssCollector()
            for feed in feeds:
                try:
                    items = await rss.collect(
                        feed_url=feed["url"],
                        source_name=feed.get("source_name", "rss"),
                        market=feed.get("market", "KR"),
                    )
                    all_items.extend(items)
                except Exception as e:
                    logger.warning("RSS collect failed for %s: %s", feed["url"], e)

        # 3. 병합된 아이템을 단일 파이프라인으로 처리
        if all_items:
            logger.info("Korean merged: %d items from all sources", len(all_items))
            db = SessionLocal()
            try:
                count = await process_collected_items(db, all_items, market="KR")
                logger.info("Korean news: %d items saved", count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
        record_job_run("kr_news_collection", "success", time.time() - start)
    except Exception as e:
        record_job_run("kr_news_collection", "failed", time.time() - start, str(e))
        logger.error("Korean news collection failed: %s", e)
        raise


def _collect_dart_disclosure_job():
    """DART 공시 수집 작업."""
    import time

    from app.core.scheduler_state import record_job_run

    if not settings.dart_api_key:
        logger.debug("DART API key not set, skipping")
        return

    logger.info("DART disclosure collection started")
    start = time.time()

    async def _run():
        from app.collectors.dart import DartCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        collector = DartCollector(api_key=settings.dart_api_key)
        items = await collector.collect()

        if items:
            db = SessionLocal()
            try:
                count = await process_collected_items(db, items, market="KR")
                logger.info("DART disclosures: %d items saved", count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
        record_job_run("dart_disclosure_collection", "success", time.time() - start)
    except Exception as e:
        record_job_run("dart_disclosure_collection", "failed", time.time() - start, str(e))
        logger.error("DART disclosure collection failed: %s", e)
        raise


def _collect_us_news_job():
    """미국 뉴스 수집 작업 (Finnhub)."""
    import time

    from app.core.scheduler_state import record_job_run

    if not settings.finnhub_api_key:
        logger.debug("Finnhub API key not set, skipping US news collection")
        return

    logger.info("US news collection started")
    start = time.time()

    async def _run():
        from app.collectors.finnhub import FinnhubCollector
        from app.collectors.pipeline import process_collected_items
        from app.core.database import SessionLocal

        collector = FinnhubCollector()
        items = await collector.collect()

        if items:
            db = SessionLocal()
            try:
                count = await process_collected_items(db, items, market="US")
                logger.info("US news: %d items saved", count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
        record_job_run("us_news_collection", "success", time.time() - start)
    except Exception as e:
        record_job_run("us_news_collection", "failed", time.time() - start, str(e))
        logger.error("US news collection failed: %s", e)
        raise


def _load_rss_feeds(market_key: str) -> list[dict]:
    """Scope 파일에서 RSS 피드 목록 로드."""
    scope = load_scope()
    return scope.get("rss_feeds", {}).get(market_key, [])


def _daily_stock_selection_job():
    """일일 종목 선정 (08:00 KST = 23:00 UTC 전날)."""
    import time

    from app.collectors.stock_selector import DynamicStockSelector
    from app.core.database import SessionLocal
    from app.core.scheduler_state import record_job_run
    from app.core.scope_loader import reload_scope
    from app.core.scope_writer import add_korean_stock, read_scope_yaml, write_scope_yaml

    logger.info("Daily stock selection started")
    start = time.time()

    try:
        db = SessionLocal()
        try:
            selector = DynamicStockSelector()
            stocks = selector.select_daily_stocks(db)

            # Update scope file with selected stocks
            data = read_scope_yaml()
            if not data:
                logger.warning("Could not read scope YAML, skipping update")
                return

            # Replace search_queries with newly selected stocks
            new_queries = [{"query": name, "stock_code": code} for name, code in stocks]
            if "korean_market" not in data:
                data["korean_market"] = {}
            data["korean_market"]["search_queries"] = new_queries
            write_scope_yaml(data)

            # Also ensure all selected stocks are in korean_stocks dict
            for name, code in stocks:
                add_korean_stock(name, code)

            # Reload scope to propagate changes
            reload_scope()

            logger.info("Daily stock selection completed: %d stocks selected", len(stocks))
        finally:
            db.close()

        record_job_run("daily_stock_selection", "success", time.time() - start)
    except Exception as e:
        record_job_run("daily_stock_selection", "failed", time.time() - start, str(e))
        logger.error("Daily stock selection failed: %s", e)
        raise


def _collect_rss_job(market_key: str):
    """RSS 피드 수집 작업."""
    feeds = _load_rss_feeds(market_key)
    if not feeds:
        logger.debug("No RSS feeds configured for %s, skipping", market_key)
        return

    market = "KR" if market_key == "korean" else "US"
    logger.info("RSS collection started: %s (%d feeds)", market_key, len(feeds))

    async def _run():
        from app.collectors.pipeline import process_collected_items
        from app.collectors.rss import RssCollector
        from app.core.database import SessionLocal

        collector = RssCollector()
        all_items = []

        for feed in feeds:
            try:
                items = await collector.collect(
                    feed_url=feed["url"],
                    source_name=feed.get("source_name", "rss"),
                    market=feed.get("market", market),
                )
                all_items.extend(items)
            except Exception as e:
                logger.warning("RSS collect failed for %s: %s", feed["url"], e)

        if all_items:
            db = SessionLocal()
            try:
                count = await process_collected_items(db, all_items, market=market)
                logger.info("RSS %s: %d items saved", market_key, count)
            finally:
                db.close()

    try:
        asyncio.run(_run())
    except Exception as e:
        logger.error("RSS %s collection failed: %s", market_key, e)


def _run_predictions_for_selected_stocks():
    """선정된 종목들에 대해 LLM 예측 실행."""
    import time

    from app.core.database import SessionLocal
    from app.core.scheduler_state import record_job_run
    from app.processing.llm_predictor import predict_with_llm

    start = time.time()
    queries = get_kr_search_queries()

    db = SessionLocal()
    try:
        success_count = 0
        for query_name, stock_code in queries:
            try:
                result = predict_with_llm(db, stock_code, market="KR")
                logger.info(
                    "Prediction for %s(%s): %s (score=%.1f, confidence=%.2f)",
                    query_name,
                    stock_code,
                    result.direction,
                    result.prediction_score,
                    result.confidence,
                )
                success_count += 1
            except Exception as e:
                logger.warning("Prediction failed for %s(%s): %s", query_name, stock_code, e)

        logger.info("Predictions completed: %d/%d stocks", success_count, len(queries))
        record_job_run("startup_predictions", "success", time.time() - start)
    except Exception as e:
        record_job_run("startup_predictions", "failed", time.time() - start, str(e))
        raise
    finally:
        db.close()


def run_startup_catchup():
    """서버 시작 후 캐치업 — 08:00 KST 이후 시작 시 즉시 종목 선정+수집+예측 실행.

    별도 스레드에서 실행되어 서버 시작을 차단하지 않습니다.
    """
    import threading
    from datetime import datetime, timedelta, timezone

    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)

    # 평일이 아니면 스킵
    if now_kst.weekday() >= 5:  # Saturday=5, Sunday=6
        logger.info("Startup catchup skipped: weekend (KST: %s)", now_kst.strftime("%A"))
        return

    # 08:00 KST 이전이면 스킵
    if now_kst.hour < 8:
        logger.info("Startup catchup skipped: before 08:00 KST (current: %02d:%02d)", now_kst.hour, now_kst.minute)
        return

    def _catchup():
        logger.info("=== Startup catchup started (KST: %s) ===", now_kst.strftime("%Y-%m-%d %H:%M"))

        try:
            # Step 1: 동적 종목 선정
            logger.info("[Catchup 1/4] Running daily stock selection...")
            _daily_stock_selection_job()
            logger.info("[Catchup 1/4] Stock selection completed")
        except Exception as e:
            logger.error("[Catchup 1/4] Stock selection failed: %s", e)

        try:
            # Step 2: KR 뉴스 수집
            logger.info("[Catchup 2/4] Collecting Korean news...")
            _collect_kr_news_job()
            logger.info("[Catchup 2/4] Korean news collection completed")
        except Exception as e:
            logger.error("[Catchup 2/4] Korean news collection failed: %s", e)

        try:
            # Step 3: US 뉴스 수집
            logger.info("[Catchup 3/4] Collecting US news...")
            _collect_us_news_job()
            logger.info("[Catchup 3/4] US news collection completed")
        except Exception as e:
            logger.error("[Catchup 3/4] US news collection failed: %s", e)

        try:
            # Step 4: LLM 예측
            logger.info("[Catchup 4/4] Running LLM predictions...")
            _run_predictions_for_selected_stocks()
            logger.info("[Catchup 4/4] Predictions completed")
        except Exception as e:
            logger.error("[Catchup 4/4] Predictions failed: %s", e)

        logger.info("=== Startup catchup finished ===")

    thread = threading.Thread(target=_catchup, name="startup-catchup", daemon=True)
    thread.start()
    logger.info("Startup catchup thread launched (runs in background)")


def create_scheduler() -> BackgroundScheduler:
    """수집 스케줄러 생성 및 job 등록."""
    scheduler = BackgroundScheduler()

    # Korean news collection job (Naver + RSS 통합)
    scheduler.add_job(
        _collect_kr_news_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_kr),
        id="kr_news_collection",
        name="Korean News Collection Job (Merged)",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    # DART disclosure collection job
    scheduler.add_job(
        _collect_dart_disclosure_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_dart),
        id="dart_disclosure_collection",
        name="DART Disclosure Collection Job",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    # US news collection job
    scheduler.add_job(
        _collect_us_news_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_us),
        id="us_news_collection",
        name="US News Collection Job",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )

    # Daily stock selection job (08:00 KST = 23:00 UTC previous day, weekdays only)
    scheduler.add_job(
        _daily_stock_selection_job,
        trigger=CronTrigger(day_of_week="mon-fri", hour=23, minute=0),
        id="daily_stock_selection",
        name="Daily Stock Selection Job",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=300,
    )

    return scheduler
