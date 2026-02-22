---
# News Collection Scope Configuration (Machine-Readable YAML Front Matter)
# 이 YAML 블록은 뉴스 수집기가 런타임에 파싱하여 사용합니다.
# 수정 시 YAML 문법을 준수하고, 하단 문서와 일관성을 유지하세요.

korean_market:
  # Naver 뉴스 검색 쿼리 목록
  search_queries:
    - query: "삼성전자"
      stock_code: "005930"
    - query: "SK하이닉스"
      stock_code: "000660"
    - query: "현대차"
      stock_code: "005380"
    - query: "NAVER"
      stock_code: "035420"
    - query: "카카오"
      stock_code: "035720"
    - query: "LG에너지솔루션"
      stock_code: "373220"
    - query: "셀트리온"
      stock_code: "068270"
    - query: "삼성바이오로직스"
      stock_code: "207940"
    - query: "기아"
      stock_code: "000270"
    - query: "POSCO홀딩스"
      stock_code: "005490"
    # 테마 대표주 추가 (Tier 1 확대)
    - query: "삼성SDI"
      stock_code: "006400"
    - query: "LG화학"
      stock_code: "051910"
    - query: "한화에어로스페이스"
      stock_code: "012450"
    - query: "HD현대중공업"
      stock_code: "329180"
    - query: "크래프톤"
      stock_code: "259960"
    - query: "KB금융"
      stock_code: "105560"
    - query: "에코프로비엠"
      stock_code: "247540"
    - query: "알테오젠"
      stock_code: "196170"
    - query: "HYBE"
      stock_code: "352820"
    - query: "한국전력"
      stock_code: "015760"

us_market:
  # Finnhub만 사용 (NewsAPI는 Finnhub과 중복으로 제거)
  finnhub:
    category: "general"

dart:
  # DART 공시는 전체 공시를 수집 후 stock_mapper로 필터링
  page_count: 100

# RSS 피드 목록 (매체당 1개 — 중복 제거)
rss_feeds:
  korean:
    - url: "https://www.yna.co.kr/rss/economy.xml"
      source_name: "rss:연합뉴스"
      market: "KR"
    - url: "https://www.hankyung.com/feed/stock"
      source_name: "rss:한국경제"
      market: "KR"
    - url: "https://www.mk.co.kr/rss/30100041/"
      source_name: "rss:매일경제"
      market: "KR"
    - url: "https://rss.edaily.co.kr/edaily/STOCK"
      source_name: "rss:이데일리"
      market: "KR"
    - url: "https://mt.co.kr/rss/stock.xml"
      source_name: "rss:머니투데이"
      market: "KR"
  # US RSS 제거 — Finnhub이 CNBC/Reuters/MarketWatch 이미 포함

# 투자 테마 키워드 사전
themes:
  AI:
    - "AI"
    - "인공지능"
    - "딥러닝"
    - "머신러닝"
    - "GPT"
    - "LLM"
    - "생성형"
  반도체:
    - "반도체"
    - "HBM"
    - "파운드리"
    - "메모리"
    - "D램"
    - "DRAM"
    - "낸드"
    - "NAND"
  2차전지:
    - "2차전지"
    - "배터리"
    - "양극재"
    - "음극재"
    - "전해질"
    - "리튬"
    - "전고체"
  바이오:
    - "바이오"
    - "신약"
    - "임상"
    - "제약"
    - "항체"
    - "세포치료"
  자동차:
    - "자동차"
    - "전기차"
    - "EV"
    - "자율주행"
    - "완성차"
  조선:
    - "조선"
    - "LNG선"
    - "컨테이너선"
    - "해운"
    - "수주"
  방산:
    - "방산"
    - "방위산업"
    - "국방"
    - "무기"
    - "K방산"
  로봇:
    - "로봇"
    - "로보틱스"
    - "자동화"
    - "휴머노이드"
  금융:
    - "금융"
    - "은행"
    - "보험"
    - "증권"
    - "핀테크"
    - "금리"
  엔터:
    - "엔터"
    - "K-POP"
    - "한류"
    - "콘텐츠"
    - "OTT"
  게임:
    - "게임"
    - "MMORPG"
    - "모바일게임"
  에너지:
    - "에너지"
    - "태양광"
    - "풍력"
    - "수소"
    - "원전"
    - "신재생"
  부동산:
    - "부동산"
    - "건설"
    - "분양"
    - "PF"
    - "주택"
  통신:
    - "통신"
    - "5G"
    - "6G"
    - "데이터센터"
    - "클라우드"
  철강:
    - "철강"
    - "포스코"
    - "고로"
    - "전기로"
  항공:
    - "항공"
    - "여행"
    - "관광"
    - "면세"

# 한국 종목 사전 (종목명 → 종목코드)
korean_stocks:
  # KOSPI 대형주
  삼성전자: "005930"
  삼성전자우: "005935"
  SK하이닉스: "000660"
  LG에너지솔루션: "373220"
  삼성바이오로직스: "207940"
  현대차: "005380"
  현대자동차: "005380"
  기아: "000270"
  셀트리온: "068270"
  KB금융: "105560"
  POSCO홀딩스: "005490"
  포스코홀딩스: "005490"
  신한지주: "055550"
  NAVER: "035420"
  네이버: "035420"
  삼성SDI: "006400"
  LG화학: "051910"
  하나금융지주: "086790"
  삼성물산: "028260"
  카카오: "035720"
  우리금융지주: "316140"
  HD현대중공업: "329180"
  HMM: "011200"
  삼성생명: "032830"
  LG전자: "066570"
  크래프톤: "259960"
  SK이노베이션: "096770"
  SK텔레콤: "017670"
  KT&G: "033780"
  한국전력: "015760"
  현대모비스: "012330"
  SK: "034730"
  한화오션: "042660"
  삼성화재: "000810"
  NH투자증권: "005940"
  두산에너빌리티: "034020"
  KT: "030200"
  LG: "003550"
  한화에어로스페이스: "012450"
  HD한국조선해양: "009540"
  한국가스공사: "036460"
  대한항공: "003490"
  에코프로비엠: "247540"
  에코프로: "086520"
  포스코퓨처엠: "003670"
  삼성전기: "009150"
  LG이노텍: "011070"
  SK바이오팜: "326030"
  카카오뱅크: "323410"
  카카오페이: "377300"
  # KOSDAQ 주요 종목
  에코프로에이치엔: "383310"
  알테오젠: "196170"
  HLB: "028300"
  리가켐바이오: "141080"
  레인보우로보틱스: "277810"
  엘앤에프: "066970"
  포스코DX: "022100"
  JYP Ent.: "035900"
  JYP엔터: "035900"
  HYBE: "352820"
  하이브: "352820"
  SM: "041510"
  펄어비스: "263750"
  CJ ENM: "035760"

# 미국 종목 사전 (Ticker → 종목명)
us_stocks:
  AAPL: "Apple"
  MSFT: "Microsoft"
  GOOGL: "Alphabet"
  AMZN: "Amazon"
  NVDA: "NVIDIA"
  META: "Meta Platforms"
  TSLA: "Tesla"
  BRK.B: "Berkshire Hathaway"
  JPM: "JPMorgan Chase"
  V: "Visa"
  UNH: "UnitedHealth"
  JNJ: "Johnson & Johnson"
  WMT: "Walmart"
  MA: "Mastercard"
  PG: "Procter & Gamble"
  HD: "Home Depot"
  XOM: "Exxon Mobil"
  AVGO: "Broadcom"
  LLY: "Eli Lilly"
  COST: "Costco"
  MRK: "Merck"
  ABBV: "AbbVie"
  PEP: "PepsiCo"
  KO: "Coca-Cola"
  ADBE: "Adobe"
  CRM: "Salesforce"
  TMO: "Thermo Fisher"
  NFLX: "Netflix"
  AMD: "AMD"
  INTC: "Intel"
  CSCO: "Cisco"
  DIS: "Disney"
  PFE: "Pfizer"
  ABT: "Abbott"
  NKE: "Nike"
  ORCL: "Oracle"
  QCOM: "Qualcomm"
  TXN: "Texas Instruments"
  IBM: "IBM"
  AMAT: "Applied Materials"
  BKNG: "Booking Holdings"
  ISRG: "Intuitive Surgical"
  NOW: "ServiceNow"
  UBER: "Uber"
  GS: "Goldman Sachs"
  BA: "Boeing"
  GE: "GE Aerospace"
  CAT: "Caterpillar"
  MMM: "3M"
  PYPL: "PayPal"

# 뉴스 스코어링 설정
scoring:
  weights:
    recency: 0.4
    frequency: 0.3
    sentiment: 0.2
    disclosure: 0.1
  recency_half_life_hours: 24
  frequency_max_count: 50

# 속보 발행 설정
breaking_news:
  threshold: 80.0
  channel_prefix: "news_breaking_"
---

# News Collection Scope (뉴스 수집 기준)

이 문서는 StockNews 시스템의 뉴스 수집 기준(scope)을 정의합니다.
상단 YAML front matter는 수집기가 런타임에 파싱하여 사용하며, 아래 Markdown은 사람이 읽는 문서입니다.

## 1. 수집 소스 및 기준

### 1.1 한국 시장 (KR)

#### Naver 뉴스 검색

| 소스 | Naver News Search (웹 스크래핑) |
|------|-------------------------------|
| URL | `https://search.naver.com/search.naver?where=news&query={검색어}` |
| 수집 주기 | 5분 (`collection_interval_kr`) |
| 검색 대상 | 시가총액 상위 20개 종목 (YAML `korean_market.search_queries` 참조) |

**검색 쿼리 목록:**

| # | 검색어 | 종목코드 |
|---|--------|----------|
| 1 | 삼성전자 | 005930 |
| 2 | SK하이닉스 | 000660 |
| 3 | 현대차 | 005380 |
| 4 | NAVER | 035420 |
| 5 | 카카오 | 035720 |
| 6 | LG에너지솔루션 | 373220 |
| 7 | 셀트리온 | 068270 |
| 8 | 삼성바이오로직스 | 207940 |
| 9 | 기아 | 000270 |
| 10 | POSCO홀딩스 | 005490 |
| 11 | 삼성SDI | 006400 |
| 12 | LG화학 | 051910 |
| 13 | 한화에어로스페이스 | 012450 |
| 14 | HD현대중공업 | 329180 |
| 15 | 크래프톤 | 259960 |
| 16 | KB금융 | 105560 |
| 17 | 에코프로비엠 | 247540 |
| 18 | 알테오젠 | 196170 |
| 19 | HYBE | 352820 |
| 20 | 한국전력 | 015760 |

#### DART 전자공시

| 소스 | DART Open API (`opendart.fss.or.kr`) |
|------|--------------------------------------|
| 수집 주기 | 5분 (`collection_interval_dart`) |
| 수집 범위 | 당일 전체 공시 (종목 필터 없음, page_count=100) |
| 종목 매핑 | 공시의 `stock_code` 필드 사용 |
| 특징 | `is_disclosure=True`로 표시 → 스코어링에서 Disclosure 가중치 적용 |

### 1.2 미국 시장 (US)

#### Finnhub News

| 소스 | Finnhub API (`finnhub.io/api/v1/news`) |
|------|----------------------------------------|
| 수집 주기 | 5분 (`collection_interval_us`) |
| 카테고리 | `general` (시장 전반 뉴스) |
| 종목 매핑 | 제목에서 ticker 추출 (`extract_tickers_from_text`) |
| 추가 기능 | `collect_company_news(symbol)` — 특정 종목 뉴스 (최근 7일) |

### 1.3 RSS 피드

| 소스 | 범용 RSS 파서 |
|------|---------------|
| 수집 주기 | 한국 KR: 5분 (Naver와 동일) |
| 피드 목록 | YAML `rss_feeds` 섹션 참조 |

#### 한국 RSS 피드 (5개, 매체당 1개)

| # | 소스 | 피드 URL |
|---|------|----------|
| 1 | 연합뉴스 경제 | `https://www.yna.co.kr/rss/economy.xml` |
| 2 | 한국경제 증권 | `https://www.hankyung.com/feed/stock` |
| 3 | 매일경제 증권 | `https://www.mk.co.kr/rss/30100041/` |
| 4 | 이데일리 증권 | `https://rss.edaily.co.kr/edaily/STOCK` |
| 5 | 머니투데이 증권 | `https://mt.co.kr/rss/stock.xml` |

> US RSS 피드는 Finnhub이 CNBC/Reuters/MarketWatch를 이미 포함하므로 제거되었습니다.

## 2. 종목 사전

### 2.1 한국 종목 (Korean Stocks)

KOSPI/KOSDAQ 주요 종목 65개 (별칭 포함). YAML `korean_stocks` 섹션 참조.

**용도:**
- 뉴스 제목에서 종목명 → 종목코드 매핑 (`stock_mapper.py`)
- 긴 이름부터 매칭하여 부분 매칭 오류 방지
- 영문명 대소문자 무시 매핑 지원

### 2.2 미국 종목 (US Stocks)

시가총액 상위 50개 종목 (Ticker → 회사명). YAML `us_stocks` 섹션 참조.

**용도:**
- 뉴스 제목에서 Ticker 추출 (`us_stock_mapper.py`)
- Word boundary 기반 정규식 매칭
- Ticker 미발견 시 회사명으로 2차 매칭

## 3. 투자 테마 분류

16개 투자 테마와 키워드. YAML `themes` 섹션 참조.

| 테마 | 키워드 수 | 주요 키워드 |
|------|----------|------------|
| AI | 7 | AI, 인공지능, GPT, LLM |
| 반도체 | 8 | 반도체, HBM, DRAM, NAND |
| 2차전지 | 7 | 배터리, 양극재, 리튬, 전고체 |
| 바이오 | 6 | 신약, 임상, 항체 |
| 자동차 | 5 | 전기차, EV, 자율주행 |
| 조선 | 5 | LNG선, 해운, 수주 |
| 방산 | 5 | 방위산업, 국방, K방산 |
| 로봇 | 4 | 로보틱스, 휴머노이드 |
| 금융 | 6 | 은행, 증권, 핀테크 |
| 엔터 | 5 | K-POP, 한류, OTT |
| 게임 | 3 | MMORPG, 모바일게임 |
| 에너지 | 6 | 태양광, 수소, 원전 |
| 부동산 | 5 | 건설, 분양, PF |
| 통신 | 5 | 5G, 데이터센터, 클라우드 |
| 철강 | 4 | 포스코, 고로, 전기로 |
| 항공 | 4 | 여행, 관광, 면세 |

**분류 방식:**
1. LLM 기반 분류 (AWS Bedrock Claude) — 기본
2. 키워드 fallback — LLM 실패 시 위 사전으로 분류

## 4. 뉴스 처리 파이프라인

```
수집 → 중복제거 → 본문 스크래핑 → 종목 매핑 → LLM 분석 → 스코어링 → DB 저장 → 속보 발행
```

| 단계 | 설명 |
|------|------|
| 1. 수집 | 각 소스별 collector가 뉴스 아이템 수집 |
| 2. 중복제거 | `source_url` 기반 DB 중복 체크 (`dedup.py`) |
| 3. 본문 스크래핑 | 기사 URL에서 본문 텍스트 추출 (`article_scraper.py`) |
| 4. 종목 매핑 | 제목/본문에서 종목코드 추출 (KR: `stock_mapper`, US: `us_stock_mapper`) |
| 5. LLM 분석 | 감성 분석 + 테마 분류 + 요약 (병렬 10 workers) |
| 6. 스코어링 | 가중합 계산 (아래 참조) |
| 7. DB 저장 | `news_event` 테이블에 저장 |
| 8. 속보 발행 | score >= threshold → Redis Pub/Sub |

## 5. 스코어링 공식

```
news_score = Recency × 0.4 + Frequency × 0.3 + Sentiment × 0.2 + Disclosure × 0.1
```

| 요소 | 가중치 | 범위 | 계산 방식 |
|------|--------|------|----------|
| Recency (최신성) | 0.4 | 0-100 | 지수 감쇠: `100 × 2^(-hours / 24)` |
| Frequency (빈도) | 0.3 | 0-100 | 선형: `min(100, count / 50 × 100)` |
| Sentiment (감성) | 0.2 | 0-100 | 선형 변환: `(score + 1) × 50` (score: -1.0~1.0) |
| Disclosure (공시) | 0.1 | 0/100 | 공시이면 100, 아니면 0 |

## 6. 속보 발행 기준

| 항목 | 값 |
|------|-----|
| 발행 임계값 | score >= **80.0** |
| Redis 채널 (KR) | `news_breaking_kr` |
| Redis 채널 (US) | `news_breaking_us` |
| 메시지 타입 | `BreakingNewsMessage` (Pydantic validated) |

## 7. 수집 주기

| 작업 | 주기 | 설정 키 |
|------|------|---------|
| 한국 뉴스 (Naver) | 5분 | `collection_interval_kr` |
| 한국 RSS | 5분 | `collection_interval_kr` |
| DART 공시 | 5분 | `collection_interval_dart` |
| 미국 뉴스 (Finnhub) | 5분 | `collection_interval_us` |

> 수집 주기는 환경 변수로도 설정 가능합니다 (`COLLECTION_INTERVAL_KR`, `COLLECTION_INTERVAL_DART`, `COLLECTION_INTERVAL_US`).

## 8. 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-02-22 | 최초 작성 — 기존 하드코딩된 수집 기준을 문서화 |
| 2026-02-22 | 중복 정리 — Naver 10→20종목, KR RSS 10→5개, US RSS/NewsAPI 제거, 수집주기 통일(5분) |
