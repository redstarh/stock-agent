# StockNews Technical Flow Documentation

Detailed technical flows for all major components of the StockNews system.

**Document Version:** 1.0
**Last Updated:** 2026-02-21
**Source Code Base:** `/Users/redstar/AgentDev/StockNews/backend/app/`

---

## Table of Contents

1. [News Collection Flow](#1-news-collection-flow)
2. [Processing Pipeline](#2-processing-pipeline)
3. [Scoring Engine](#3-scoring-engine)
4. [API Request Handling](#4-api-request-handling)
5. [WebSocket Flow](#5-websocket-flow)
6. [ML Training Flow](#6-ml-training-flow)

---

## 1. News Collection Flow

### 1.1 Overview

The system collects news from three primary sources:
- **Korean Market:** Naver News (web scraping) + DART Disclosures (API)
- **US Market:** Finnhub News API + NewsAPI

Collection runs on scheduled intervals managed by APScheduler.

### 1.2 Naver Collector (Korean News)

**File:** `app/collectors/naver.py`

**Step-by-Step Flow:**

```
START: NaverCollector.collect(query, stock_code, market="KR")
  │
  ├─→ 1. Build search URL
  │     URL: https://search.naver.com/search.naver
  │     Params: {where: "news", query: "삼성전자", sm: "tab_jum"}
  │
  ├─→ 2. Retry loop (max_retries=3)
  │     │
  │     ├─→ 3. Send HTTP GET request (httpx.AsyncClient)
  │     │
  │     ├─→ 4. Check HTTP status
  │     │     ├─ Success (200) → Continue
  │     │     └─ Error → Log warning, retry with exponential backoff
  │     │           delay = base_delay * (2 ** attempt)
  │     │
  │     ├─→ 5. Parse HTML with BeautifulSoup
  │     │     Target: <a data-heatmap-target=".tit">
  │     │
  │     ├─→ 6. Extract news items
  │     │     For each <a> tag:
  │     │       - Extract href (source_url)
  │     │       - Extract text (title)
  │     │       - Skip if duplicate URL (seen_urls set)
  │     │
  │     └─→ 7. Build item dict
  │           {
  │             "title": "...",
  │             "source_url": "https://...",
  │             "source": "naver",
  │             "market": "KR",
  │             "stock_code": "005930"
  │           }
  │
  └─→ 8. Return items list (or empty list if all retries failed)
```

**Error Handling:**
- `httpx.HTTPStatusError`: Retry with exponential backoff
- `httpx.RequestError`: Retry with exponential backoff
- After 3 failures: Return empty list, log error

**Performance:**
- Async operation (httpx.AsyncClient)
- Exponential backoff: 1s, 2s, 4s
- No caching (always fresh data)

---

### 1.3 DART Collector (Korean Disclosures)

**File:** `app/collectors/dart.py`

**Step-by-Step Flow:**

```
START: DartCollector.collect(begin_date)
  │
  ├─→ 1. Set date range
  │     If begin_date not provided:
  │       begin_date = datetime.now(UTC).strftime("%Y%m%d")
  │
  ├─→ 2. Build API request
  │     URL: https://opendart.fss.or.kr/api/list.json
  │     Params: {
  │       crtfc_key: API_KEY,
  │       bgn_de: "20260221",
  │       page_count: "100"
  │     }
  │
  ├─→ 3. Send HTTP GET (httpx.AsyncClient)
  │     ├─ Success → Parse JSON
  │     └─ Error → Log error, return empty list
  │
  ├─→ 4. Validate response
  │     Check: data["status"] == "000"
  │     If not: Log warning, return empty list
  │
  ├─→ 5. Parse disclosure entries
  │     For each entry in data["list"]:
  │       {
  │         "title": entry["report_nm"],
  │         "stock_code": entry["stock_code"],
  │         "stock_name": entry["corp_name"],
  │         "source": "dart",
  │         "source_url": "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=...",
  │         "market": "KR",
  │         "is_disclosure": True,
  │         "published_at": parse_dart_date(entry["rcept_dt"])
  │       }
  │
  └─→ 6. Return items list
```

**Date Parsing:**
```python
def _parse_dart_date(date_str: str) -> datetime | None:
    # Input: "20260221" (8 chars)
    # Output: datetime(2026, 2, 21, tzinfo=UTC)
    if len(date_str) != 8:
        return None
    return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=UTC)
```

**Error Handling:**
- API error (status != "000"): Log warning, return empty list
- Network error: Log error, return empty list
- Date parsing error: Set published_at to None

---

### 1.4 Finnhub Collector (US News)

**File:** `app/collectors/finnhub.py`

**Step-by-Step Flow:**

```
START: FinnhubCollector.collect(category="general", min_id=0)
  │
  ├─→ 1. Check API key
  │     If not set: Log warning, return empty list
  │
  ├─→ 2. Build API request
  │     URL: https://finnhub.io/api/v1/news
  │     Params: {
  │       category: "general",
  │       token: API_KEY,
  │       minId: 0
  │     }
  │
  ├─→ 3. Retry loop (max_retries=3)
  │     │
  │     ├─→ 4. Send HTTP GET
  │     │
  │     ├─→ 5. Parse JSON response
  │     │     Response: [
  │     │       {
  │     │         "headline": "...",
  │     │         "url": "...",
  │     │         "datetime": 1708531200,  // Unix timestamp
  │     │         "source": "Reuters"
  │     │       }
  │     │     ]
  │     │
  │     ├─→ 6. Extract stock tickers from headline
  │     │     Function: extract_tickers_from_text(headline)
  │     │     Uses regex: r'\b([A-Z]{1,5})\b'
  │     │     Example: "Apple (AAPL) releases..." → ["AAPL"]
  │     │
  │     ├─→ 7. Convert Unix timestamp to ISO
  │     │     datetime.fromtimestamp(raw["datetime"], tz=UTC).isoformat()
  │     │
  │     └─→ 8. Build item dict
  │           {
  │             "title": headline,
  │             "source_url": url,
  │             "source": "finnhub:Reuters",
  │             "market": "US",
  │             "stock_code": "AAPL",
  │             "published_at": "2026-02-21T09:00:00+00:00"
  │           }
  │
  └─→ 9. Return items (or retry on error)
```

**Company-Specific News:**
```
FinnhubCollector.collect_company_news(symbol="AAPL", from_date, to_date)
  │
  ├─→ 1. Set date range (default: last 7 days)
  ├─→ 2. API endpoint: /company-news
  ├─→ 3. Filter: symbol="AAPL", from="2026-02-14", to="2026-02-21"
  └─→ 4. Return items with stock_code pre-filled
```

---

### 1.5 Scheduler System

**File:** `app/collectors/scheduler.py`

**Scheduler Architecture:**

```
APScheduler (BackgroundScheduler)
  │
  ├─→ Job 1: Korean News Collection
  │     Trigger: IntervalTrigger(minutes=1)
  │     ID: "kr_news_collection"
  │     Max Instances: 1
  │     Misfire Grace Time: 30s
  │     │
  │     └─→ _collect_kr_news_job()
  │           │
  │           ├─→ For each (query, stock_code) in KR_SEARCH_QUERIES:
  │           │     NaverCollector.collect(query, stock_code)
  │           │     Aggregate all_items
  │           │
  │           └─→ process_collected_items(db, all_items, market="KR")
  │
  ├─→ Job 2: DART Disclosure Collection
  │     Trigger: IntervalTrigger(minutes=5)
  │     ID: "dart_disclosure_collection"
  │     │
  │     └─→ _collect_dart_disclosure_job()
  │           │
  │           ├─→ DartCollector.collect()
  │           └─→ process_collected_items(db, items, market="KR")
  │
  └─→ Job 3: US News Collection
        Trigger: IntervalTrigger(minutes=5)
        ID: "us_news_collection"
        │
        └─→ _collect_us_news_job()
              │
              ├─→ FinnhubCollector.collect()
              └─→ process_collected_items(db, items, market="US")
```

**Top Korean Stocks Monitored:**
```python
KR_SEARCH_QUERIES = [
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
```

**Async Execution Pattern:**
```python
def _collect_kr_news_job():
    # Scheduler job runs in thread pool
    # Must wrap async code
    async def _run():
        # Async collection logic
        ...

    # Run async code in event loop
    asyncio.run(_run())
```

---

## 2. Processing Pipeline

### 2.1 Pipeline Overview

**File:** `app/collectors/pipeline.py`

The processing pipeline transforms raw collected news into structured, analyzed data ready for scoring.

```
INPUT: Raw news items from collectors
  │
  ├─→ PHASE 1: Deduplication
  ├─→ PHASE 2: Article Scraping
  ├─→ PHASE 3: Preprocessing
  ├─→ PHASE 4: LLM Analysis (Parallel)
  ├─→ PHASE 5: Database Storage + Redis Pub/Sub
  │
OUTPUT: Saved NewsEvent records
```

---

### 2.2 PHASE 1: Deduplication

**File:** `app/processing/dedup.py`

**Algorithm:**

```
deduplicate(db, items: list[dict]) -> list[dict]
  │
  ├─→ 1. Initialize tracking
  │     unique = []
  │     seen_urls = set()
  │
  ├─→ 2. For each item in items:
  │     │
  │     ├─→ 2a. Batch-level dedup check
  │     │     If item.source_url in seen_urls:
  │     │       SKIP (duplicate within batch)
  │     │
  │     ├─→ 2b. Database-level dedup check
  │     │     Query: NewsEvent.filter(source_url == item.source_url)
  │     │     If exists: SKIP
  │     │
  │     │     Query: NewsEvent.filter(title == item.title)
  │     │     If exists: SKIP (same news from different source)
  │     │
  │     ├─→ 2c. Add to unique list
  │     │     unique.append(item)
  │     │     seen_urls.add(item.source_url)
  │     │
  │     └─→ 3. Return unique items
```

**Priority Order:**
1. URL-based dedup (most reliable)
2. Title-based dedup (catches syndicated news)
3. Batch-internal dedup (efficiency optimization)

**Performance:**
- O(n) time complexity with set lookups
- Two DB queries per item (can be optimized with batch query)

---

### 2.3 PHASE 2: Article Scraping

**File:** `app/processing/article_scraper.py`

**Batch Scraping Flow:**

```
ArticleScraper.scrape_batch(items: list[dict]) -> dict[str, ScrapeResult]
  │
  ├─→ 1. Skip sources
  │     If item.source == "dart": Skip (DART has no body)
  │
  ├─→ 2. Create async tasks
  │     For each item:
  │       tasks.append(scrape_one(item.source_url, item.source))
  │
  ├─→ 3. Execute with concurrency limit
  │     Semaphore(MAX_CONCURRENT_REQUESTS=5)
  │     Results = await asyncio.gather(*tasks)
  │
  └─→ 4. Return URL → ScrapeResult mapping
```

**Single URL Scraping:**

```
scrape_one(url: str, source: str) -> ScrapeResult
  │
  ├─→ 1. Fetch HTML
  │     httpx.AsyncClient.get(url)
  │     Timeout: 10s
  │     User-Agent: "Mozilla/5.0 ... StockNews/1.0"
  │     Follow redirects: True
  │
  ├─→ 2. Validate content-type
  │     Must contain: "text/html" or "application/xhtml"
  │
  ├─→ 3. Parse with BeautifulSoup
  │     parser: "html.parser"
  │
  ├─→ 4. Remove noise tags
  │     Tags: ["script", "style", "iframe", "nav", "header", "footer", "aside"]
  │     soup.find_all(tag).decompose()
  │
  ├─→ 5. Extract body text (site-specific)
  │     │
  │     ├─→ 5a. Try site-specific selector
  │     │     news.naver.com → "#dic_area"
  │     │     n.news.naver.com → "#newsct_article"
  │     │     www.hankyung.com → "#articletxt"
  │     │     www.mk.co.kr → "#article_body"
  │     │     (more in SITE_SELECTORS)
  │     │
  │     ├─→ 5b. Try fallback selectors
  │     │     ["article", '[itemprop="articleBody"]', ".article-body", ...]
  │     │     Stop at first match with len(text) > 100
  │     │
  │     └─→ 5c. Try paragraph aggregation
  │           soup.find_all("p")
  │           Combine all <p> texts
  │           Accept if len > 100
  │
  ├─→ 6. Clean text
  │     Replace: \s+ → single space
  │     Strip leading/trailing whitespace
  │
  ├─→ 7. Truncate to max length
  │     body = body[:MAX_BODY_LENGTH=3000]
  │
  └─→ 8. Return ScrapeResult(url, body, error=None)
```

**Error Handling:**
- Timeout → `ScrapeResult(url, body=None, error="timeout")`
- HTTP error → `ScrapeResult(url, body=None, error="http_404")`
- Parse error → `ScrapeResult(url, body=None, error="parse_error")`

---

### 2.4 PHASE 3: Preprocessing

**File:** `app/collectors/pipeline.py` (process_collected_items)

**Preprocessing Steps:**

```
For each unique_item:
  │
  ├─→ 1. Extract fields
  │     title = item.get("title", "")
  │     source_url = item.get("source_url", "")
  │     source = item.get("source", "unknown")
  │     is_disclosure = item.get("is_disclosure", False)
  │     published_at = item.get("published_at")
  │
  ├─→ 2. Normalize published_at
  │     If string: datetime.fromisoformat(published_at)
  │     If None: datetime.now(UTC)
  │     Ensure timezone-aware
  │
  ├─→ 3. Map stock code
  │     │
  │     ├─→ 3a. If stock_code provided: Use it
  │     │
  │     ├─→ 3b. If market == "US":
  │     │     extract_tickers_from_text(title)
  │     │     Regex: r'\b([A-Z]{1,5})\b'
  │     │     Example: "Apple (AAPL)" → "AAPL"
  │     │
  │     └─→ 3c. If market == "KR":
  │           extract_stock_codes(title)
  │           Lookup in STOCK_DICT (hardcoded dictionary)
  │           Example: "삼성전자 실적" → "005930"
  │
  ├─→ 4. Get stock name
  │     If market == "US":
  │       ticker_to_name(stock_code)
  │     If market == "KR":
  │       code_to_name(stock_code)
  │
  ├─→ 5. Retrieve scraped body
  │     body = body_map.get(source_url)
  │
  └─→ 6. Build prepared dict
        {
          "title": title,
          "source_url": source_url,
          "source": source,
          "is_disclosure": is_disclosure,
          "published_at": published_at,
          "stock_code": stock_code,
          "stock_name": stock_name,
          "body": body
        }
```

**Stock Mapping Example (KR):**

```python
STOCK_DICT = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "현대차": "005380",
    # ... (75+ major stocks)
}

def extract_stock_codes(text: str) -> list[str]:
    # Sort by length (longest first) to avoid partial matches
    # "삼성전자우" must match before "삼성전자"
    sorted_names = sorted(STOCK_DICT.keys(), key=len, reverse=True)

    codes = []
    for name in sorted_names:
        if name in text:
            code = STOCK_DICT[name]
            codes.append(code)

    return codes
```

---

### 2.5 PHASE 4: LLM Analysis (Parallel)

**File:** `app/collectors/pipeline.py` (_analyze_single)

**Parallel Execution Architecture:**

```
ThreadPoolExecutor(max_workers=10)
  │
  ├─→ For each prepared_item:
  │     Submit: _analyze_single(title, body, market)
  │     Thread-safe LLM calls
  │
  └─→ Collect results with as_completed()
```

**Single Item Analysis:**

```
_analyze_single(title: str, body: str | None, market: str) -> dict
  │
  ├─→ 1. Sentiment Analysis
  │     │
  │     ├─→ Call: analyze_sentiment(title, body)
  │     │     Model: AWS Bedrock Claude (Sonnet 4 via mid model)
  │     │
  │     │     System Prompt:
  │     │       "당신은 한국 금융 시장 전문 감성 분석가입니다."
  │     │
  │     │     Few-shot examples:
  │     │       Input: "삼성전자 4분기 영업이익 10조원 돌파"
  │     │       Output: {"sentiment": "positive", "score": 0.85, "confidence": 0.95}
  │     │
  │     │     Input text:
  │     │       "제목: {title}\n본문: {body[:2000]}"
  │     │
  │     │     Response:
  │     │       {"sentiment": "positive"|"neutral"|"negative",
  │     │        "score": -1.0 ~ 1.0,
  │     │        "confidence": 0.0 ~ 1.0}
  │     │
  │     └─→ Fallback on error:
  │           {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
  │
  ├─→ 2. Theme Classification
  │     │
  │     ├─→ Primary: LLM-based classification
  │     │     Call: classify_theme_llm(title, body, model_id=Opus)
  │     │
  │     │     System Prompt:
  │     │       "다음 뉴스의 투자 테마를 분류하세요."
  │     │       Available themes: AI, 반도체, 2차전지, 바이오, ...
  │     │
  │     │     Response: ["AI", "반도체"]
  │     │
  │     └─→ Fallback: Keyword matching
  │           classify_theme(title + body[:500])
  │           THEME_KEYWORDS = {
  │             "AI": ["AI", "인공지능", "딥러닝", "GPT"],
  │             "반도체": ["반도체", "HBM", "메모리"],
  │             ...
  │           }
  │
  ├─→ 3. News Summary (if body exists)
  │     Call: summarize_news(title, body)
  │     Model: AWS Bedrock Claude Opus
  │
  │     System Prompt:
  │       "다음 뉴스를 2-3문장으로 요약하세요."
  │
  │     Response: "삼성전자가 4분기 영업이익 10조원을 돌파하며..."
  │
  │     Fallback: summary = ""
  │
  ├─→ 4. Cross-market Analysis (US news only)
  │     If market == "US":
  │       Call: analyze_kr_impact(title, body)
  │       Identifies Korean stocks affected by US news
  │
  │       Example:
  │         Input: "NVIDIA announces new AI chip"
  │         Output: ["AI", "반도체"] (impacts Korean semiconductor stocks)
  │
  └─→ 5. Return analysis dict
        {
          "sentiment": "positive",
          "sentiment_score": 0.85,
          "themes": ["AI", "반도체"],
          "summary": "...",
          "kr_impact_themes": ["AI", "반도체"]  // US news only
        }
```

**Progress Logging:**
```python
# Log every 50 items to track progress
if done_count % 50 == 0:
    logger.info("LLM progress: %d/%d", done_count, len(prepared))
```

---

## 3. Scoring Engine

### 3.1 Score Formula

**File:** `app/scoring/engine.py`

**Overall Formula:**
```
News Score = (Recency × 0.4) + (Frequency × 0.3) + (Sentiment × 0.2) + (Disclosure × 0.1)

Where:
  Recency: 0-100 (time decay)
  Frequency: 0-100 (news volume)
  Sentiment: 0-100 (sentiment mapping)
  Disclosure: 0 or 100 (bonus)
```

---

### 3.2 Recency Component

**Exponential Decay Model:**

```python
def calc_recency(published_at: datetime, reference: datetime | None = None) -> float:
    """
    Score = 100 × 2^(-hours / half_life)

    Where:
      half_life = 24 hours
      hours = (reference - published_at).total_seconds() / 3600
    """

    HALF_LIFE_HOURS = 24.0

    # Calculate time delta
    delta_hours = (reference - published_at).total_seconds() / 3600.0

    # Future date → clamp to 100
    if delta_hours < 0:
        return 100.0

    # Exponential decay
    score = 100.0 * math.pow(2, -delta_hours / HALF_LIFE_HOURS)

    return round(max(0.0, min(100.0, score)), 2)
```

**Decay Examples:**
```
Time Ago    | Score
------------|-------
0 hours     | 100.0
12 hours    | 70.7
24 hours    | 50.0
48 hours    | 25.0
72 hours    | 12.5
168 hours   | 0.78
```

---

### 3.3 Frequency Component

**Linear Scaling:**

```python
def calc_frequency(news_count: int) -> float:
    """
    Score = min(100, count / max_count × 100)

    Where:
      max_count = 50 (saturation point)
    """

    MAX_COUNT = 50

    if news_count <= 0:
        return 0.0

    score = (news_count / MAX_COUNT) * 100.0

    return round(min(100.0, score), 2)
```

**Frequency Examples:**
```
News Count | Score
-----------|-------
1          | 2.0
5          | 10.0
10         | 20.0
25         | 50.0
50         | 100.0
100        | 100.0 (capped)
```

---

### 3.4 Sentiment Component

**Score Normalization:**

```python
def calc_sentiment_score(sentiment: str, score: float) -> float:
    """
    Maps -1.0 ~ 1.0 range to 0-100 range

    Formula: (score + 1.0) × 50
    """

    normalized = (score + 1.0) * 50.0

    return round(max(0.0, min(100.0, normalized)), 2)
```

**Sentiment Mapping:**
```
LLM Score | Normalized | Meaning
----------|------------|----------
-1.0      | 0.0        | Very negative
-0.5      | 25.0       | Negative
0.0       | 50.0       | Neutral
0.5       | 75.0       | Positive
1.0       | 100.0      | Very positive
```

---

### 3.5 Disclosure Component

**Binary Bonus:**

```python
def calc_disclosure(is_disclosure: bool) -> float:
    """
    Disclosure bonus: 100 if True, 0 if False
    """
    return 100.0 if is_disclosure else 0.0
```

**Rationale:**
- Official disclosures (DART) are high-signal events
- 10% weight gives ~10 point boost to disclosed news
- Example: Regular news (70) vs Disclosed news (80)

---

### 3.6 Final Score Calculation

**Weighted Sum:**

```python
def calc_news_score(
    recency: float,
    frequency: float,
    sentiment: float,
    disclosure: float,
) -> float:
    """
    Weighted average with predefined weights
    """

    W_RECENCY = 0.4
    W_FREQUENCY = 0.3
    W_SENTIMENT = 0.2
    W_DISCLOSURE = 0.1

    score = (
        recency * W_RECENCY
        + frequency * W_FREQUENCY
        + sentiment * W_SENTIMENT
        + disclosure * W_DISCLOSURE
    )

    return round(max(0.0, min(100.0, score)), 2)
```

**Example Calculation:**

```
Input:
  recency = 70.7       (12 hours old)
  frequency = 20.0     (10 news items)
  sentiment = 75.0     (positive, score=0.5)
  disclosure = 0.0     (not a disclosure)

Calculation:
  score = 70.7 × 0.4 + 20.0 × 0.3 + 75.0 × 0.2 + 0.0 × 0.1
  score = 28.28 + 6.0 + 15.0 + 0.0
  score = 49.28

Output: 49.28
```

---

## 4. API Request Handling

### 4.1 GET /news/score

**File:** `app/api/news.py`

**Request Flow:**

```
GET /api/v1/news/score?stock=005930
  │
  ├─→ 1. Authentication
  │     Middleware: verify_api_key(request)
  │     Check: X-API-Key header
  │     Fallback: api_key query parameter
  │
  ├─→ 2. Rate Limiting
  │     Limiter: 60 requests/minute
  │     Key: client IP address
  │     If exceeded: HTTP 429 Too Many Requests
  │
  ├─→ 3. Parameter Validation
  │     Required: stock (string)
  │     Pydantic validation
  │
  ├─→ 4. Database Query
  │     Query: SELECT * FROM news_event
  │            WHERE stock_code = '005930'
  │     Result: List of NewsEvent objects
  │
  ├─→ 5. Calculate Aggregates
  │     │
  │     ├─→ 5a. Average score
  │     │     avg_score = sum(r.news_score for r in rows) / len(rows)
  │     │
  │     ├─→ 5b. Average sentiment
  │     │     avg_sentiment = sum(r.sentiment_score for r in rows) / len(rows)
  │     │
  │     ├─→ 5c. Count by sentiment
  │     │     positive_count = count where sentiment == "positive"
  │     │     negative_count = count where sentiment == "negative"
  │     │     neutral_count = total - positive - negative
  │     │
  │     ├─→ 5d. Top 3 themes
  │     │     theme_counts = Counter([r.theme for r in rows])
  │     │     top_themes = theme_counts.most_common(3)
  │     │
  │     ├─→ 5e. Latest update
  │     │     updated_at = max(r.published_at for r in rows)
  │     │
  │     └─→ 5f. Disclosure count
  │           disclosure = sum(1 for r in rows if r.is_disclosure)
  │
  ├─→ 6. Build Response
  │     NewsScoreResponse(
  │       stock_code="005930",
  │       stock_name="삼성전자",
  │       news_score=82.5,
  │       recency=70.7,
  │       frequency=20.0,
  │       sentiment_score=0.75,
  │       disclosure=2,
  │       news_count=10,
  │       positive_count=7,
  │       neutral_count=2,
  │       negative_count=1,
  │       top_themes=["AI", "반도체"],
  │       updated_at="2026-02-21T09:00:00+00:00"
  │     )
  │
  └─→ 7. Return JSON (FastAPI auto-serialization)
```

**Response Schema:**
```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "news_score": 82.5,
  "recency": 70.7,
  "frequency": 20.0,
  "sentiment_score": 0.75,
  "disclosure": 2,
  "news_count": 10,
  "positive_count": 7,
  "neutral_count": 2,
  "negative_count": 1,
  "top_themes": ["AI", "반도체"],
  "updated_at": "2026-02-21T09:00:00+00:00"
}
```

---

### 4.2 GET /news/top

**Request Flow:**

```
GET /api/v1/news/top?market=KR&limit=10
  │
  ├─→ 1. Authentication + Rate Limiting (same as /news/score)
  │
  ├─→ 2. Database Aggregation Query
  │     Query:
  │       SELECT
  │         stock_code,
  │         stock_name,
  │         AVG(news_score) as avg_score,
  │         AVG(sentiment_score) as avg_sentiment,
  │         MAX(sentiment) as sentiment,
  │         COUNT(*) as cnt,
  │         market
  │       FROM news_event
  │       WHERE market = 'KR'
  │       GROUP BY stock_code, stock_name, market
  │
  ├─→ 3. Calculate Prediction Scores
  │     For each row:
  │       prediction_score = min(100, max(0,
  │         avg_score × 0.6 + (avg_sentiment + 1) × 20
  │       ))
  │
  │       direction = "up" if prediction_score > 60
  │                   "down" if prediction_score < 40
  │                   else "neutral"
  │
  ├─→ 4. Sort by Prediction Score (descending)
  │
  ├─→ 5. Limit Results (top N)
  │
  └─→ 6. Return Response
        [
          {
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "news_score": 82.5,
            "sentiment": "positive",
            "news_count": 15,
            "market": "KR",
            "prediction_score": 85.0,
            "direction": "up"
          },
          ...
        ]
```

---

### 4.3 GET /news/latest

**Request Flow:**

```
GET /api/v1/news/latest?market=KR&limit=20&offset=0
  │
  ├─→ 1. Authentication + Rate Limiting
  │
  ├─→ 2. Build Query with Filters
  │     Base: SELECT * FROM news_event
  │
  │     Filters:
  │       - market: WHERE market = 'KR'
  │       - stock: WHERE stock_code ILIKE '%term%' OR stock_name ILIKE '%term%'
  │       - sentiment: WHERE sentiment = 'positive'
  │       - theme: WHERE theme ILIKE '%AI%'
  │       - date_from: WHERE DATE(published_at) >= '2026-02-01'
  │       - date_to: WHERE DATE(published_at) <= '2026-02-21'
  │
  │     Order: ORDER BY published_at DESC
  │     Pagination: OFFSET 0 LIMIT 20
  │
  ├─→ 3. Execute Query
  │     Total count query (for pagination info)
  │     Data query (with offset/limit)
  │
  ├─→ 4. Map to Response Schema
  │     For each row:
  │       NewsItem(
  │         id=row.id,
  │         title=row.title,
  │         stock_code=row.stock_code,
  │         stock_name=row.stock_name,
  │         sentiment=row.sentiment,
  │         news_score=row.news_score,
  │         source=row.source,
  │         source_url=row.source_url,
  │         market=row.market,
  │         theme=row.theme,
  │         content=row.content,
  │         summary=row.summary,
  │         published_at=row.published_at
  │       )
  │
  └─→ 5. Return Paginated Response
        {
          "items": [...],
          "total": 150,
          "offset": 0,
          "limit": 20
        }
```

---

## 5. WebSocket Flow

### 5.1 Connection Establishment

**File:** `app/api/websocket.py`

**Connection Flow:**

```
Client: new WebSocket("ws://localhost:8001/ws/news")
  │
  ├─→ 1. Server accepts connection
  │     await ws.accept()
  │
  ├─→ 2. Check connection limit
  │     If len(active_connections) >= MAX_WS_CONNECTIONS (100):
  │       Send: {"type": "error", "message": "max connections exceeded"}
  │       Close connection
  │       STOP
  │
  ├─→ 3. Add to active connections
  │     _active_connections.append(ws)
  │
  ├─→ 4. Start Redis subscriber (if first client)
  │     If len(active_connections) == 1:
  │       Start background task: subscribe_and_broadcast()
  │
  ├─→ 5. Send welcome message
  │     Send: {"type": "connected", "message": "StockNews WebSocket connected"}
  │
  └─→ 6. Enter message loop (see Message Handling)
```

---

### 5.2 Message Handling

**Client → Server Messages:**

```
Message Loop:
  │
  ├─→ Receive: await ws.receive_json()
  │
  ├─→ Parse message type
  │     │
  │     └─→ If type == "ping":
  │           Send: {"type": "pong"}
  │
  └─→ On disconnect or error:
        │
        ├─→ Remove from active connections
        │
        └─→ If last client disconnected:
              Stop Redis subscriber task
```

---

### 5.3 Redis Pub/Sub Integration

**File:** `app/core/pubsub.py`

**Publisher Flow (Breaking News):**

```
publish_news_event(redis_client, news_event, score)
  │
  ├─→ 1. Check threshold
  │     If score < BREAKING_THRESHOLD (80.0):
  │       Return False (don't publish)
  │
  ├─→ 2. Build message payload
  │     message = BreakingNewsMessage(
  │       stock_code=news_event.stock_code,
  │       stock_name=news_event.stock_name,
  │       title=news_event.title,
  │       theme=news_event.theme,
  │       sentiment=news_event.sentiment_score,
  │       news_score=score,
  │       market=news_event.market,
  │       published_at=news_event.published_at.isoformat()
  │     )
  │
  ├─→ 3. Validate with Pydantic
  │     If validation error:
  │       Log error, Return False
  │
  ├─→ 4. Determine channel
  │     channel = "news_breaking_kr"  // if market == "KR"
  │     channel = "news_breaking_us"  // if market == "US"
  │
  ├─→ 5. Publish to Redis
  │     redis_client.publish(channel, message.model_dump_json())
  │
  └─→ 6. Log and return True
```

**Subscriber Flow (WebSocket Broadcast):**

```
subscribe_and_broadcast(redis_client, broadcast_callback)
  │
  ├─→ 1. Subscribe to channels
  │     pubsub = redis_client.pubsub()
  │     await pubsub.subscribe("news_breaking_kr", "news_breaking_us")
  │
  ├─→ 2. Listen loop
  │     async for message in pubsub.listen():
  │       │
  │       ├─→ 3. Filter message type
  │       │     If message["type"] != "message":
  │       │       Continue
  │       │
  │       ├─→ 4. Parse JSON
  │       │     raw_data = json.loads(message["data"])
  │       │
  │       ├─→ 5. Validate schema
  │       │     validated = validate_message(raw_data)
  │       │     If validation fails:
  │       │       Log warning, Continue
  │       │
  │       ├─→ 6. Broadcast to all WebSocket clients
  │       │     await broadcast_callback(validated.model_dump())
  │       │
  │       └─→ Error handling:
  │             - JSONDecodeError → Log, Continue
  │             - ValidationError → Log, Continue
  │             - Broadcast error → Log, Continue
  │
  └─→ 3. On exception or task cancel:
        await pubsub.close()
```

---

### 5.4 Broadcast Mechanism

**File:** `app/api/websocket.py` (broadcast function)

**Broadcast Flow:**

```
broadcast(message: dict)
  │
  ├─→ 1. Iterate active connections
  │     For each ws in _active_connections:
  │       │
  │       ├─→ Try send
  │       │     await ws.send_json(message)
  │       │
  │       └─→ On error:
  │             Mark for disconnection
  │             disconnected.append(ws)
  │
  └─→ 2. Cleanup disconnected clients
        For each ws in disconnected:
          _remove_connection(ws)
```

**Message Examples:**

```json
// Breaking news event
{
  "type": "breaking_news",
  "data": {
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "title": "삼성전자 4분기 영업이익 10조원 돌파",
    "news_score": 90,
    "theme": "AI",
    "sentiment": 0.85,
    "market": "KR",
    "published_at": "2026-02-21T09:00:00+00:00"
  }
}

// Ping/Pong
{
  "type": "ping"
}
→ Response:
{
  "type": "pong"
}
```

---

### 5.5 Reconnection Logic (Client-Side)

**Recommended Client Pattern:**

```javascript
class NewsWebSocket {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectDelay = 1000; // Start with 1s
    this.maxReconnectDelay = 30000; // Max 30s
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("Connected");
      this.reconnectDelay = 1000; // Reset delay
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    this.ws.onclose = () => {
      console.log("Disconnected, reconnecting...");
      this.stopHeartbeat();
      this.reconnect();
    };
  }

  reconnect() {
    setTimeout(() => {
      this.connect();
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2,
        this.maxReconnectDelay
      );
    }, this.reconnectDelay);
  }

  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Every 30s
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }

  handleMessage(message) {
    switch (message.type) {
      case "connected":
        console.log("Welcome:", message.message);
        break;
      case "breaking_news":
        this.onBreakingNews(message.data);
        break;
      case "pong":
        console.log("Heartbeat OK");
        break;
    }
  }
}
```

---

## 6. ML Training Flow

### 6.1 Training Data Preparation

**File:** `app/processing/training_data_builder.py`

**Data Collection Flow:**

```
build_training_dataset(stock_codes, db, days=30)
  │
  ├─→ For each stock_code:
  │     │
  │     ├─→ 1. Collect news features
  │     │     Query: SELECT * FROM news_event
  │     │            WHERE stock_code = code
  │     │            AND created_at >= (now - days)
  │     │
  │     │     Aggregate:
  │     │       - avg(news_score)
  │     │       - avg(sentiment_score)
  │     │       - count(*)
  │     │       - avg(news_score) WHERE created_at >= (now - 3days)
  │     │       - sum(is_disclosure) / count(*)
  │     │
  │     ├─→ 2. Collect price features
  │     │     API: yfinance / KRX
  │     │     Calculate:
  │     │       - price_change_pct (5-day)
  │     │       - volume_change_pct
  │     │       - moving_average_ratio (20-day MA)
  │     │
  │     ├─→ 3. Build feature vector
  │     │     features = [
  │     │       news_score,          # 0-100
  │     │       sentiment_score,     # -1.0 ~ 1.0
  │     │       news_count,          # integer
  │     │       avg_score_3d,        # 0-100
  │     │       disclosure_ratio,    # 0.0 ~ 1.0
  │     │       price_change_pct,    # percentage
  │     │       volume_change_pct,   # percentage
  │     │       moving_average_ratio # ratio
  │     │     ]
  │     │
  │     └─→ 4. Generate label
  │           If price_change_pct > 2.0:
  │             label = "up"
  │           Elif price_change_pct < -2.0:
  │             label = "down"
  │           Else:
  │             label = "neutral"
  │
  └─→ 5. Save to training table
        INSERT INTO stock_training_data (
          stock_code,
          market,
          prediction_date,
          news_score,
          sentiment_score,
          news_count,
          avg_score_3d,
          disclosure_ratio,
          price_change_pct,
          volume_change_pct,
          moving_average_ratio,
          actual_direction  -- "up" | "down" | "neutral"
        )
```

---

### 6.2 Feature Engineering

**File:** `app/processing/feature_engineer.py`

**Feature Extraction:**

```
build_feature_vector(stock_code, db, collector)
  │
  ├─→ 1. News Features (30-day window)
  │     │
  │     ├─→ news_score (float)
  │     │     Average of all news_score values
  │     │
  │     ├─→ sentiment_score (float)
  │     │     Average of sentiment_score (-1.0 ~ 1.0)
  │     │
  │     ├─→ news_count (int)
  │     │     Total number of news items
  │     │
  │     ├─→ avg_score_3d (float)
  │     │     Average news_score for last 3 days
  │     │     (captures recent momentum)
  │     │
  │     └─→ disclosure_ratio (float)
  │           Count of disclosures / total news
  │           Range: 0.0 ~ 1.0
  │
  └─→ 2. Price Features (5-day window)
        │
        ├─→ price_change_pct (float)
        │     (current_price - price_5d_ago) / price_5d_ago * 100
        │
        ├─→ volume_change_pct (float)
        │     (avg_volume_5d - avg_volume_30d) / avg_volume_30d * 100
        │
        └─→ moving_average_ratio (float)
              current_price / moving_average_20d
              > 1.0: Above MA (bullish)
              < 1.0: Below MA (bearish)
```

---

### 6.3 Model Training

**File:** `app/processing/ml_trainer.py`

**Training Pipeline:**

```
MLTrainer(market="KR", tier=1)
  │
  ├─→ 1. Load training data
  │     Query: SELECT * FROM stock_training_data
  │            WHERE market = 'KR'
  │            AND actual_direction IS NOT NULL
  │            ORDER BY prediction_date  -- Time-series order!
  │
  │     Minimum samples: 100 (Tier 1)
  │
  │     If insufficient: Raise ValueError
  │
  ├─→ 2. Prepare X and y
  │     X = pd.DataFrame with feature columns
  │     y = pd.Series with labels ("up", "neutral", "down")
  │
  ├─→ 3. Choose algorithm
  │     │
  │     ├─→ Option A: LightGBM
  │     │     model = LGBMClassifier(
  │     │       n_estimators=100,
  │     │       max_depth=5,
  │     │       learning_rate=0.1,
  │     │       num_leaves=31
  │     │     )
  │     │
  │     └─→ Option B: Random Forest
  │           model = RandomForestClassifier(
  │             n_estimators=100,
  │             max_depth=10
  │           )
  │
  ├─→ 4. Cross-validation (TimeSeriesSplit)
  │     │
  │     ├─→ Split data chronologically
  │     │     TimeSeriesSplit(n_splits=5)
  │     │
  │     │     Example with 100 samples:
  │     │       Fold 1: Train[0:20]   → Test[20:40]
  │     │       Fold 2: Train[0:40]   → Test[40:60]
  │     │       Fold 3: Train[0:60]   → Test[60:80]
  │     │       Fold 4: Train[0:80]   → Test[80:100]
  │     │
  │     │       NEVER: Random shuffle (data leakage!)
  │     │
  │     ├─→ Train and evaluate each fold
  │     │     For each split:
  │     │       model.fit(X_train, y_train)
  │     │       score = model.score(X_test, y_test)
  │     │       scores.append(score)
  │     │
  │     └─→ Calculate CV metrics
  │           cv_accuracy = mean(scores)
  │           cv_std = std(scores)
  │
  ├─→ 5. Final training (full dataset)
  │     model.fit(X, y)
  │
  ├─→ 6. Extract feature importances
  │     importances = model.feature_importances_
  │
  │     Example output:
  │       {
  │         "news_score": 0.25,
  │         "sentiment_score": 0.20,
  │         "price_change_pct": 0.18,
  │         "avg_score_3d": 0.15,
  │         "moving_average_ratio": 0.12,
  │         "news_count": 0.05,
  │         "volume_change_pct": 0.03,
  │         "disclosure_ratio": 0.02
  │       }
  │
  └─→ 7. Save model
        │
        ├─→ Serialize with pickle
        │     data = pickle.dumps(model)
        │
        ├─→ Generate SHA-256 checksum
        │     checksum = hashlib.sha256(data).hexdigest()
        │
        ├─→ Save to file
        │     Path: models/lightgbm_KR_t1_v1.0.0.pkl
        │
        └─→ Record in database
              INSERT INTO ml_model (
                name="lightgbm",
                version="1.0.0",
                market="KR",
                tier=1,
                accuracy=0.65,
                cv_accuracy=0.62,
                cv_std=0.04,
                checksum="abc123...",
                created_at=now
              )
```

---

### 6.4 Hyperparameter Tuning

**File:** `app/processing/ml_trainer.py` (tune_hyperparameters)

**Optuna Optimization:**

```
tune_hyperparameters(X, y, model_type="lightgbm", n_trials=30)
  │
  ├─→ 1. Define objective function
  │     def objective(trial):
  │       │
  │       ├─→ 1a. Suggest hyperparameters
  │       │     params = {
  │       │       "n_estimators": trial.suggest_int("n_estimators", 50, 300),
  │       │       "max_depth": trial.suggest_int("max_depth", 3, 10),
  │       │       "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
  │       │       "num_leaves": trial.suggest_int("num_leaves", 15, 63),
  │       │       ...
  │       │     }
  │       │
  │       ├─→ 1b. Create model
  │       │     model = LGBMClassifier(**params)
  │       │
  │       ├─→ 1c. Evaluate with TimeSeriesSplit CV
  │       │     tscv = TimeSeriesSplit(n_splits=5)
  │       │     scores = cross_val_score(model, X, y, cv=tscv, scoring="accuracy")
  │       │
  │       └─→ 1d. Return mean accuracy
  │             return mean(scores)
  │
  ├─→ 2. Create Optuna study
  │     study = optuna.create_study(direction="maximize")
  │
  ├─→ 3. Run optimization
  │     study.optimize(objective, n_trials=30, timeout=300)
  │
  │     Progress:
  │       Trial 1/30: accuracy=0.58, params={...}
  │       Trial 2/30: accuracy=0.61, params={...}
  │       ...
  │       Trial 30/30: accuracy=0.65, params={...}
  │
  └─→ 4. Return best results
        {
          "best_params": {
            "n_estimators": 150,
            "max_depth": 7,
            "learning_rate": 0.05,
            "num_leaves": 31
          },
          "best_accuracy": 0.65,
          "best_trial": 23,
          "n_trials_completed": 30
        }
```

---

### 6.5 Model Evaluation

**File:** `app/processing/ml_evaluator.py`

**Evaluation Metrics:**

```
evaluate_model(model, X_test, y_test)
  │
  ├─→ 1. Predict
  │     y_pred = model.predict(X_test)
  │
  ├─→ 2. Calculate metrics
  │     │
  │     ├─→ Accuracy
  │     │     accuracy = accuracy_score(y_test, y_pred)
  │     │     Example: 0.65 (65% correct predictions)
  │     │
  │     ├─→ Confusion Matrix
  │     │     confusion_matrix(y_test, y_pred)
  │     │
  │     │     Predicted: up  neutral  down
  │     │     Actual up:    20       5       2
  │     │     Actual neutral: 8      15       3
  │     │     Actual down:    3       4      10
  │     │
  │     ├─→ Precision, Recall, F1 per class
  │     │     classification_report(y_test, y_pred)
  │     │
  │     │     Class      Precision  Recall  F1-Score
  │     │     up            0.65     0.74     0.69
  │     │     neutral       0.63     0.58     0.60
  │     │     down          0.67     0.59     0.63
  │     │
  │     └─→ ROC-AUC (multi-class)
  │           roc_auc_score(y_test, y_pred_proba, multi_class="ovr")
  │
  └─→ 3. Return evaluation dict
        {
          "accuracy": 0.65,
          "confusion_matrix": [[20, 5, 2], [8, 15, 3], [3, 4, 10]],
          "classification_report": {...},
          "roc_auc": 0.72
        }
```

---

### 6.6 Prediction Flow

**File:** `app/processing/prediction.py`

**Inference Flow:**

```
predict_stock_movement(stock_code, market, db)
  │
  ├─→ 1. Load model from registry
  │     Query: SELECT * FROM ml_model
  │            WHERE market = 'KR'
  │            AND is_active = True
  │            ORDER BY version DESC
  │            LIMIT 1
  │
  │     Load: MLTrainer.load_model(filepath, expected_checksum)
  │
  ├─→ 2. Build feature vector
  │     features = build_feature_vector(stock_code, db, collector)
  │     X = [[
  │       features["news_score"],
  │       features["sentiment_score"],
  │       features["news_count"],
  │       features["avg_score_3d"],
  │       features["disclosure_ratio"],
  │       features["price_change_pct"],
  │       features["volume_change_pct"],
  │       features["moving_average_ratio"]
  │     ]]
  │
  ├─→ 3. Make prediction
  │     y_pred = model.predict(X)  # ["up"] or ["down"] or ["neutral"]
  │     y_proba = model.predict_proba(X)  # [[0.7, 0.2, 0.1]]
  │
  ├─→ 4. Calculate prediction score
  │     # Heuristic: weighted combination
  │     prediction_score = min(100, max(0,
  │       features["news_score"] * 0.6 + (features["sentiment_score"] + 1) * 20
  │     ))
  │
  └─→ 5. Return prediction result
        {
          "stock_code": "005930",
          "predicted_direction": "up",
          "probabilities": {
            "up": 0.70,
            "neutral": 0.20,
            "down": 0.10
          },
          "prediction_score": 85.0,
          "confidence": 0.70,
          "features": {...}
        }
```

---

## Appendix: Performance Metrics

### Collection Performance

| Collector | Avg Time | Max Items | Retry Logic |
|-----------|----------|-----------|-------------|
| Naver | 1-2s | ~10/query | 3 retries, exponential backoff |
| DART | 2-3s | 100 | Single attempt |
| Finnhub | 1-2s | 50 | 3 retries, exponential backoff |

### Processing Performance

| Stage | Avg Time | Parallelism |
|-------|----------|-------------|
| Deduplication | <0.1s/100 items | Sequential |
| Article Scraping | 2-5s/item | 5 concurrent |
| LLM Analysis | 3-5s/item | 10 parallel threads |
| Database Save | <0.1s/item | Sequential |

### API Performance

| Endpoint | Avg Response Time | Cache Hit Rate |
|----------|-------------------|----------------|
| /news/score | 50-100ms | N/A (realtime) |
| /news/top | 100-200ms | N/A (aggregation) |
| /news/latest | 50-150ms | N/A (filtered query) |

### Model Performance

| Model | Accuracy | CV Accuracy | Training Time |
|-------|----------|-------------|---------------|
| LightGBM | 65-70% | 62-67% | 30-60s |
| Random Forest | 60-65% | 58-63% | 60-120s |

---

**END OF DETAILED_FLOWS.md**
