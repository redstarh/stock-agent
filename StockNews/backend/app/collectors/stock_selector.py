"""동적 종목 선정 엔진.

매일 장 시작 전(08:00 KST) 실행하여 5가지 전략으로 최대 30개 종목을 선정합니다.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.scope_loader import load_scope
from app.models.news_event import NewsEvent
from app.models.theme_strength import ThemeStrength

logger = logging.getLogger(__name__)


class DynamicStockSelector:
    """5가지 신호를 결합한 동적 종목 선정기."""

    BASE_STOCK_LIMIT = 10       # 시총 상위 (항상 포함)
    THEME_STOCK_LIMIT = 8       # 트렌딩 테마 대표주
    VOLUME_ANOMALY_LIMIT = 5    # 거래량 이상 종목
    NEWS_MOMENTUM_LIMIT = 4     # 뉴스 모멘텀 종목
    DART_DISCLOSURE_LIMIT = 3   # 최근 24h 공시 종목
    MAX_TOTAL_QUERIES = 30      # 하드 캡

    def select_daily_stocks(self, db: Session) -> list[tuple[str, str]]:
        """5개 전략 결합, 중복 제거, 최대 30개 반환.

        Returns:
            list of (query_name, stock_code) tuples
        """
        selected: dict[str, str] = {}  # stock_code -> query_name (dedup by code)

        # Strategy 1: Base stocks (always included, top 10 from scope)
        base = self._select_base_stocks()
        for name, code in base:
            if code not in selected:
                selected[code] = name

        # Strategy 2: Theme trending stocks
        theme = self._select_theme_trending(db)
        for name, code in theme:
            if code not in selected:
                selected[code] = name

        # Strategy 3: Volume anomaly
        volume = self._select_volume_anomaly(list(selected.keys()))
        for name, code in volume:
            if code not in selected:
                selected[code] = name

        # Strategy 4: News momentum
        momentum = self._select_news_momentum(db)
        for name, code in momentum:
            if code not in selected:
                selected[code] = name

        # Strategy 5: DART disclosure
        dart = self._select_dart_disclosure(db)
        for name, code in dart:
            if code not in selected:
                selected[code] = name

        # Apply hard cap
        result = [(name, code) for code, name in selected.items()]
        if len(result) > self.MAX_TOTAL_QUERIES:
            result = result[:self.MAX_TOTAL_QUERIES]

        logger.info(
            "Daily stock selection: %d stocks (base=%d, theme=%d, volume=%d, momentum=%d, dart=%d)",
            len(result), len(base), len(theme), len(volume), len(momentum), len(dart),
        )
        return result

    def _select_base_stocks(self) -> list[tuple[str, str]]:
        """전략 1: scope의 search_queries 상위 N개 (시총 상위)."""
        scope = load_scope()
        queries = scope.get("korean_market", {}).get("search_queries", [])
        result = []
        for q in queries[:self.BASE_STOCK_LIMIT]:
            result.append((q["query"], q["stock_code"]))
        return result

    def _select_theme_trending(self, db: Session) -> list[tuple[str, str]]:
        """전략 2: 최근 3일 theme_strength 상위 테마 → 대표주.

        Top themes by strength_score → map to representative stocks from korean_stocks dict.
        """
        three_days_ago = datetime.now(UTC).date() - timedelta(days=3)

        # Get top themes by average strength_score over last 3 days
        top_themes = (
            db.query(
                ThemeStrength.theme,
                func.avg(ThemeStrength.strength_score).label("avg_strength"),
            )
            .filter(
                ThemeStrength.market == "KR",
                ThemeStrength.date >= three_days_ago,
            )
            .group_by(ThemeStrength.theme)
            .order_by(func.avg(ThemeStrength.strength_score).desc())
            .limit(5)
            .all()
        )

        if not top_themes:
            return []

        # Load theme→keyword and stock mappings from scope
        scope = load_scope()
        themes_dict = scope.get("themes", {})
        korean_stocks = scope.get("korean_stocks", {})

        # For each top theme, find representative stocks
        # Strategy: match theme keywords against stock names
        result = []
        # Build a theme->stocks mapping based on known associations
        theme_stock_map = self._build_theme_stock_map(themes_dict, korean_stocks)

        for theme_row in top_themes:
            theme_name = theme_row.theme
            # theme_name might be comma-separated like "AI,반도체"
            for single_theme in theme_name.split(","):
                single_theme = single_theme.strip()
                if single_theme in theme_stock_map:
                    for name, code in theme_stock_map[single_theme][:2]:  # Max 2 per theme
                        result.append((name, code))
                        if len(result) >= self.THEME_STOCK_LIMIT:
                            return result

        return result[:self.THEME_STOCK_LIMIT]

    def _build_theme_stock_map(
        self, themes_dict: dict, korean_stocks: dict
    ) -> dict[str, list[tuple[str, str]]]:
        """테마별 대표 종목 매핑 구축."""
        # Known theme-stock associations
        THEME_STOCKS = {
            "AI": ["삼성전자", "SK하이닉스", "네이버", "카카오", "크래프톤"],
            "반도체": ["삼성전자", "SK하이닉스", "삼성SDI", "삼성전기"],
            "2차전지": ["LG에너지솔루션", "삼성SDI", "에코프로비엠", "에코프로", "LG화학", "엘앤에프"],
            "바이오": ["삼성바이오로직스", "셀트리온", "알테오젠", "SK바이오팜", "HLB"],
            "자동차": ["현대차", "기아", "현대모비스"],
            "조선": ["HD현대중공업", "HD한국조선해양", "한화오션"],
            "방산": ["한화에어로스페이스", "LG이노텍"],
            "로봇": ["레인보우로보틱스", "삼성전자"],
            "금융": ["KB금융", "신한지주", "하나금융지주", "우리금융지주"],
            "엔터": ["HYBE", "JYP Ent.", "SM", "CJ ENM"],
            "게임": ["크래프톤", "펄어비스"],
            "에너지": ["한국전력", "두산에너빌리티", "한국가스공사"],
            "부동산": ["삼성물산"],
            "통신": ["SK텔레콤", "KT", "네이버"],
            "철강": ["POSCO홀딩스", "포스코퓨처엠"],
            "항공": ["대한항공", "HMM"],
        }

        result = {}
        for theme, stock_names in THEME_STOCKS.items():
            stocks = []
            for name in stock_names:
                code = korean_stocks.get(name)
                if code:
                    stocks.append((name, code))
            if stocks:
                result[theme] = stocks

        return result

    def _select_volume_anomaly(self, existing_codes: list[str]) -> list[tuple[str, str]]:
        """전략 3: 거래량 이상 종목 (5일 평균 / 20일 평균 > 2.0).

        Only checks stocks already in scope + theme stocks (not entire korean_stocks).
        Uses PriceCollector with cache.
        """
        from app.collectors.price_collector import PriceCollector

        scope = load_scope()
        queries = scope.get("korean_market", {}).get("search_queries", [])
        korean_stocks = scope.get("korean_stocks", {})

        # Candidate pool: current scope queries that aren't already selected
        candidates = []
        for q in queries:
            code = q["stock_code"]
            if code not in existing_codes:
                candidates.append((q["query"], code))

        # Also add some stocks from korean_stocks not already in scope
        scope_codes = {q["stock_code"] for q in queries}
        for name, code in korean_stocks.items():
            if code not in existing_codes and code not in scope_codes:
                candidates.append((name, code))
                if len(candidates) >= 40:  # Cap candidates to limit API calls
                    break

        collector = PriceCollector(cache_ttl=300)
        anomalies = []

        for name, code in candidates:
            try:
                df = collector.fetch_price_history(code, period="1mo")
                if df is None or len(df) < 20:
                    continue

                recent_5d_vol = df.tail(5)["volume"].mean()
                avg_20d_vol = df.tail(20)["volume"].mean()

                if avg_20d_vol > 0 and recent_5d_vol / avg_20d_vol > 2.0:
                    anomalies.append((name, code, recent_5d_vol / avg_20d_vol))
            except Exception as e:
                logger.debug("Volume check failed for %s: %s", name, e)

        # Sort by volume ratio descending
        anomalies.sort(key=lambda x: x[2], reverse=True)
        return [(name, code) for name, code, _ in anomalies[:self.VOLUME_ANOMALY_LIMIT]]

    def _select_news_momentum(self, db: Session) -> list[tuple[str, str]]:
        """전략 4: 최근 24h 뉴스 건수 급증 + 평균 스코어 상위."""
        since = datetime.now(UTC) - timedelta(hours=24)

        results = (
            db.query(
                NewsEvent.stock_code,
                NewsEvent.stock_name,
                func.count(NewsEvent.id).label("news_count"),
                func.avg(NewsEvent.news_score).label("avg_score"),
            )
            .filter(
                NewsEvent.market == "KR",
                NewsEvent.created_at >= since,
                NewsEvent.stock_code.isnot(None),
                NewsEvent.stock_code != "",
            )
            .group_by(NewsEvent.stock_code, NewsEvent.stock_name)
            .having(func.count(NewsEvent.id) >= 3)  # Minimum 3 news items
            .order_by(func.count(NewsEvent.id).desc(), func.avg(NewsEvent.news_score).desc())
            .limit(self.NEWS_MOMENTUM_LIMIT)
            .all()
        )

        return [(r.stock_name or r.stock_code, r.stock_code) for r in results if r.stock_code]

    def _select_dart_disclosure(self, db: Session) -> list[tuple[str, str]]:
        """전략 5: 최근 24h 공시 발생 종목."""
        since = datetime.now(UTC) - timedelta(hours=24)

        results = (
            db.query(
                NewsEvent.stock_code,
                NewsEvent.stock_name,
                func.count(NewsEvent.id).label("disclosure_count"),
            )
            .filter(
                NewsEvent.market == "KR",
                NewsEvent.is_disclosure == True,  # noqa: E712
                NewsEvent.created_at >= since,
                NewsEvent.stock_code.isnot(None),
                NewsEvent.stock_code != "",
            )
            .group_by(NewsEvent.stock_code, NewsEvent.stock_name)
            .order_by(func.count(NewsEvent.id).desc())
            .limit(self.DART_DISCLOSURE_LIMIT)
            .all()
        )

        return [(r.stock_name or r.stock_code, r.stock_code) for r in results if r.stock_code]
