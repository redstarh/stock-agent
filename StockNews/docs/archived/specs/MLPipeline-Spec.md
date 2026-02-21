# ML Pipeline Enhancement Specification v2

> **v2 Changes:** Feature analysis review 반영. 53개 → 20개 피처로 축소.
> 유해/중복/노이즈 피처 25개 제거. 단계별 검증(Tiered) 접근법 적용.

---

## 1. Overview

### 1.1 Current State

| Item | Status |
|------|--------|
| Model | RandomForestClassifier (8 features) |
| Features | news_score, sentiment, news_count, avg_score_3d, disclosure_ratio, price_change_pct, volume_change_pct, ma_ratio |
| Training Data | `stock_training_data` table (32 columns, 10 records) |
| Technical Indicators | RSI(14), Bollinger Band, Volatility(5d), MA5/MA20 ratios |
| Accuracy | ~60% (10 sample KR stocks, single day) |
| Markets | KR, US |

### 1.2 Target

Accuracy targets with 95% confidence intervals. Statistical significance required (p < 0.05 vs baseline).

| Phase | Target Accuracy | Sample Size | Feature Count |
|-------|----------------|-------------|---------------|
| Phase 0 | Baseline 확인 | 200+ | 8 (Tier 1) |
| Phase 1 | 58-62% (95% CI) | 200-500 | 8 (Tier 1) |
| Phase 2 | 60-65% (95% CI) | 500+ | 16 (Tier 1+2) |
| Phase 3 | 62-68% (95% CI) | 1000+ | 20 (Tier 1+2+3) |
| Phase 4 | 65-70% (stretch) | 1000+ | 최적화 |

- **Baseline:** "항상 neutral 예측" = ~33% (3-class)
- **성공 기준:** Accuracy > baseline + 15% with p < 0.05
- **Professional ceiling:** 55-65% (이 이상은 과적합 의심)

### 1.3 Strategy

```
Phase 0: Data Sprint      → 200+ labeled samples 수집 (PREREQUISITE)
Phase 1: Tier 1 Model     → 핵심 8개 피처 + LightGBM
Phase 2: Tier 2 Expansion → +8개 피처 (배치별 A/B 검증)
Phase 3: Tier 3 + Frontend → +4개 피처 + ML Dashboard
Phase 4: Optimization     → 자동 피처 선택, 하이퍼파라미터 튜닝
```

### 1.4 Critical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Data scarcity (10 samples) | CRITICAL | Phase 0 data sprint, backfill |
| yfinance reliability | HIGH | Retry middleware, FinanceDataReader fallback |
| Overfitting (features > N/10) | HIGH | Tiered approach, max 8 features for N=200 |
| KRX API unavailability | HIGH | OPTIONAL, pykrx if legal |
| Unrealistic accuracy targets | MEDIUM | CI, statistical testing, professional ceiling 인식 |

---

## 2. Feature Engineering Specification

### 2.1 Design Principles

1. **N/10 Rule:** 샘플 수의 1/10 이하 피처만 사용
2. **Incremental Validation:** 피처 배치 추가 시 A/B 테스트 필수
3. **변화율 > 절대값:** 방향 예측에는 변화율만 의미 있음
4. **중복 제거:** 같은 신호를 측정하는 지표는 하나만 유지
5. **노이즈 최소화:** 2차 도함수, 극단적 희소 피처 배제

### 2.2 Feature Tiers

#### Tier 1: 핵심 8개 (N=200부터, Phase 1)

| # | Feature | Category | Source | Rationale |
|---|---------|----------|--------|-----------|
| 1 | `news_score` | News | existing | 제품 핵심, recency+frequency+sentiment 복합 |
| 2 | `sentiment_score` | News | existing | 감성→1일 방향 효과 (Tetlock 2007) |
| 3 | `rsi_14` | Technical | existing | 가장 강력한 평균회귀 신호 |
| 4 | `prev_change_pct` | Price | existing | 단기 평균회귀/모멘텀 |
| 5 | `price_change_5d` | Price | existing | 다일 모멘텀 (Jegadeesh & Titman 1993) |
| 6 | `volume_change_5d` | Price | existing | 이상 거래량 = 움직임 선행 |
| 7 | `market_return` | Market | NEW | KOSPI(KR) 또는 S&P500(US) 전일 등락률 |
| 8 | `vix_change` | Market | NEW | 공포 지표 변화, 단기 예측력 |

> `market_return`은 기존 `market_index_change`를 대체. KR 종목은 KOSPI, US 종목은 S&P500 값 사용.

#### Tier 2: 확장 8개 (N=500부터, Phase 2)

배치별로 추가하며, 각 배치 추가 후 CV 정확도 비교.

**Batch A: 뉴스 심화 (3개)**

| # | Feature | Rationale |
|---|---------|-----------|
| 9 | `news_count_3d` | 최근 3일 뉴스 건수 (관심도 급변) |
| 10 | `avg_score_3d` | 최근 3일 평균 점수 (지속성) |
| 11 | `sentiment_trend` | 3일-7일 감성 차이 (모멘텀) |

**Batch B: 주가 심화 (2개)**

| # | Feature | Rationale |
|---|---------|-----------|
| 12 | `ma5_ratio` | 5일 이평선 대비 현재가 (추세) |
| 13 | `volatility_5d` | 5일 변동성 (리스크) |

**Batch C: 시장/공시 (3개)**

| # | Feature | Rationale |
|---|---------|-----------|
| 14 | `usd_krw_change` | 환율 변동 (KR 시장 민감) |
| 15 | `has_earnings_disclosure` | 실적 공시 여부 (이벤트) |
| 16 | `cross_theme_score` | 동일 테마 타 종목 평균 스코어 |

#### Tier 3: 고급 4개 (N=1000부터, Phase 3)

| # | Feature | Condition | Source |
|---|---------|-----------|--------|
| 17 | `foreign_net_ratio` | KRX 데이터 확보 시 | KRX/pykrx |
| 18 | `sector_index_change` | 업종 분류 정확 시 | yfinance |
| 19 | `disclosure_ratio` | DART 데이터 축적 시 | DART API |
| 20 | `bb_position` | RSI 보완 효과 확인 시 | yfinance |

#### Conditional: A/B 테스트 후 결정 (8개)

| Feature | 포함 조건 |
|---------|----------|
| `news_count` | news_count_3d와 중복 여부 확인 |
| `ma20_ratio` | ma5_ratio 보완 효과 확인 |
| `is_monday` | 월요일 효과 유의미 시 |
| `has_major_disclosure` | 실적 외 공시 효과 확인 |
| `macd_histogram` | RSI 보완 효과 확인 |
| `obv_change` | volume_change_5d 보완 확인 |
| `news_velocity_6h` | 6시간 속도 유의미 시 |
| `vix_value` | VIX 수준별 레짐 효과 확인 |

### 2.3 제거된 피처와 사유

#### 예측을 적극적으로 방해하는 피처 (8개)

| Feature | 문제 | 메커니즘 |
|---------|------|---------|
| `prev_close` | 주가 수준 ≠ 방향 | 허위 상관: 종목 크기 학습 |
| `prev_volume` | 절대 거래량 ≠ 방향 | 허위 상관: 종목 크기 학습 |
| `individual_net_buy` | = -(foreign+institution) | 선형 종속: 수치 불안정 |
| `news_acceleration` | 노이즈의 미분 | 2차 도함수 = 노이즈 증폭 |
| `stochastic_k/d` | RSI와 동일 측정 | 다중공선성 (r~0.6) |
| `days_to_month_end` | 방향과 무관한 숫자 | 허위 split point 학습 |
| `news_velocity_1h` | 1시간 = 0 or 1건 | 극단적 노이즈 |
| `nasdaq_change` | S&P500과 r~0.9 | 심각한 다중공선성 |

#### 중복 제거 (10쌍 → 제거 대상)

| 제거 | 유지 | 이유 |
|------|------|------|
| `market_index_change` | `market_return` | 같은 지수, 명칭 통일 |
| `day_of_week` | (제거) | 정수 인코딩 오류, is_monday가 나음 |
| `vix_value` | `vix_change` | 변화가 신호 |
| `atr_14` | `volatility_5d` | r~0.7, 단순한 것 유지 |
| `ma60_ratio` | `ma5_ratio` | 60일은 1일 예측에 너무 느림 |
| `macd_signal` | (conditional) | histogram이 나음 |
| `foreign_net_buy` | `foreign_net_ratio` | 비율이 종목 크기 정규화 |
| `institution_net_buy` | `foreign_net_ratio` | 외국인과 역상관 |
| `theme_momentum` | `cross_theme_score` | 파생값 불필요 |
| `disclosure_count_7d` | `has_earnings_disclosure` | 유형이 건수보다 중요 |

#### 신호 없음 (7개)

| Feature | 사유 |
|---------|------|
| `is_friday` | 금요일 효과 미입증 |
| `is_month_end` | 효과 < 0.3%, 거래비용 이하 |
| `is_quarter_end` | 연 4회, 학습 불가 |
| `gold_change` | 주식과 불안정한 관계 (r~0.05) |
| `crude_oil_change` | 에너지 섹터만 유효 |
| `foreign_holding_pct` | 일간 변동 < 0.1%, 변별력 없음 |
| `news_count` (30d) | news_count_3d가 더 적합 |

---

## 3. Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────┐
│              Data Collection Layer                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Market   │  │ DART     │  │ Theme    │      │
│  │ Indicator│  │ Enhanced │  │ Analyzer │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       └──────────────┴─────────────┘             │
│                      │                           │
│          ┌───────────▼───────────┐               │
│          │  Feature Store        │               │
│          │  (StockTrainingData)  │               │
│          │  Tier 1→2→3 columns  │               │
│          └───────────┬───────────┘               │
│                      │                           │
│          ┌───────────▼───────────┐               │
│          │  ML Training Layer    │               │
│          │  ┌──────┐ ┌────────┐ │               │
│          │  │ LGBM │ │   RF   │ │               │
│          │  └──┬───┘ └───┬────┘ │               │
│          │     └────┬────┘      │               │
│          │  ┌───────▼────────┐  │               │
│          │  │ Model Evaluator│  │               │
│          │  └───────┬────────┘  │               │
│          └──────────┼───────────┘               │
│                     │                            │
│          ┌──────────▼────────────┐               │
│          │  Prediction + Verify   │               │
│          └──────────┬────────────┘               │
│                     │                            │
│          ┌──────────▼────────────┐               │
│          │  Frontend Dashboard    │               │
│          └───────────────────────┘               │
└─────────────────────────────────────────────────┘
```

### 3.2 Module Structure

```
backend/app/
├── collectors/
│   ├── market_indicator_collector.py   # NEW: VIX, index, FX (library module)
│   └── dart_collector.py              # MODIFY: earnings disclosure flag
├── processing/
│   ├── technical_indicators.py        # existing (no changes needed)
│   ├── training_data_builder.py       # MODIFY: Tier 1→2→3 features
│   ├── feature_config.py              # NEW: Tier definitions, feature metadata
│   ├── feature_validator.py           # NEW: Bounds check, null imputation
│   ├── cross_theme_scorer.py          # NEW: Theme-level scoring
│   ├── ml_trainer.py                  # NEW: LightGBM + RF pipeline
│   ├── ml_evaluator.py               # NEW: Model comparison, A/B test
│   └── model_registry.py             # NEW: Model versioning
├── models/
│   ├── training.py                    # MODIFY: Tier columns only
│   └── ml_model.py                    # NEW: Model metadata table
├── schemas/
│   └── training.py                    # MODIFY: Extended schemas
└── api/
    └── training.py                    # MODIFY: ML endpoints
```

> **Architecture Decision:** `market_indicator_collector`는 **library module**.
> `training_data_builder`가 import하여 호출. 별도 스케줄러 단계 아님.
> 이렇게 하면 중복 API 호출을 방지하고, 같은 날의 시장 지표를 전 종목이 공유.

### 3.3 Data Flow

```
1. Scheduler triggers daily (KR: 16:00 KST, US: 17:00 EST)
2. training_data_builder.build_training_snapshot()
   └── market_indicator_collector.fetch_batch()  (1회, 캐시)
   └── technical_indicators.compute_*()
   └── feature_validator.validate()
   └── StockTrainingData에 저장
3. verification_engine.run_verification() → 실제 결과 업데이트
4. ml_trainer.retrain() → 주간 재학습 (200+ samples 이상 시)
5. ml_evaluator.compare() → 모델 비교, 최적 선택
6. Prediction API → 활성 모델로 예측
```

### 3.4 Database Schema

#### StockTrainingData 변경 (기존 32열 → 정리)

**제거할 기존 컬럼:** (기존 데이터에는 남기되, ML에서 사용하지 않음)
- `prev_close`, `prev_volume` — 절대값, 방향 예측 무관
- `market_index_change` — `market_return`으로 대체
- `day_of_week` — 정수 인코딩 오류

**추가 컬럼 (Phase 1 — Tier 1):**

```sql
ALTER TABLE stock_training_data ADD COLUMN market_return FLOAT;
ALTER TABLE stock_training_data ADD COLUMN vix_change FLOAT;
```

**추가 컬럼 (Phase 2 — Tier 2):**

```sql
ALTER TABLE stock_training_data ADD COLUMN usd_krw_change FLOAT;
ALTER TABLE stock_training_data ADD COLUMN has_earnings_disclosure BOOLEAN DEFAULT FALSE;
ALTER TABLE stock_training_data ADD COLUMN cross_theme_score FLOAT DEFAULT 0;
```

> `news_count_3d`, `avg_score_3d`, `sentiment_trend`, `ma5_ratio`, `volatility_5d`는 이미 존재.

**추가 컬럼 (Phase 3 — Tier 3):**

```sql
ALTER TABLE stock_training_data ADD COLUMN foreign_net_ratio FLOAT;
ALTER TABLE stock_training_data ADD COLUMN sector_index_change FLOAT;
```

> `disclosure_ratio`, `bb_position`은 이미 존재.

**ML Model Registry:**

```sql
CREATE TABLE ml_model (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    market VARCHAR(5) NOT NULL,
    feature_tier INTEGER NOT NULL,         -- 1, 2, or 3
    feature_list TEXT NOT NULL,            -- JSON array
    train_accuracy FLOAT,
    test_accuracy FLOAT,
    cv_accuracy FLOAT,
    cv_std FLOAT,                          -- CV 표준편차
    train_samples INTEGER,
    test_samples INTEGER,
    train_start_date DATE,
    train_end_date DATE,
    is_active BOOLEAN DEFAULT FALSE,
    model_path VARCHAR(500),
    model_checksum VARCHAR(64),            -- SHA-256
    hyperparameters TEXT,
    feature_importances TEXT,
    created_at DATETIME NOT NULL,
    UNIQUE(model_name, model_version, market)
);
CREATE INDEX ix_ml_model_active ON ml_model(is_active, market);
```

**추가 인덱스:**

```sql
CREATE INDEX idx_training_labels ON stock_training_data(market, prediction_date, actual_direction);
```

---

## 4. TDD Strategy

### 4.1 Test-First Approach

```
1. Write failing test (expected behavior)
2. Implement minimal code to pass
3. Refactor while green
4. Edge case tests
5. Coverage >= 80%
```

### 4.2 Test Plan

| Module | Test File | Tests | Coverage |
|--------|-----------|-------|----------|
| market_indicator_collector | test_market_indicator_collector.py | 8 | 90% |
| feature_config | test_feature_config.py | 6 | 95% |
| feature_validator | test_feature_validator.py | 10 | 95% |
| cross_theme_scorer | test_cross_theme_scorer.py | 6 | 90% |
| ml_trainer | test_ml_trainer.py | 12 | 85% |
| ml_evaluator | test_ml_evaluator.py | 8 | 85% |
| model_registry | test_model_registry.py | 6 | 90% |
| training_data_builder (ext) | test_training_data_builder.py | +6 | 85% |
| training API (ext) | test_training_api.py | +8 | 85% |
| backfill script | test_training_backfill.py | 4 | 80% |
| **Total** | | **~74 new** | **88% avg** |

### 4.3 Critical Test Cases

```python
# 1. Tier 1 피처만으로 모델 학습 가능 확인
def test_train_with_tier1_only():
    """8 features, 200 samples → accuracy > 50%"""

# 2. Tier 2 추가 시 정확도 향상 확인
def test_tier2_improves_accuracy():
    """Tier1+2 accuracy > Tier1-only accuracy (p < 0.05)"""

# 3. 유해 피처 포함 시 정확도 하락 확인
def test_harmful_features_degrade():
    """prev_close 추가 시 CV accuracy 하락"""

# 4. TimeSeriesSplit 사용 확인
def test_no_data_leakage():
    """Train dates < test dates (never random split)"""

# 5. Feature validation bounds
def test_rsi_bounds():
    """RSI must be 0-100, reject outliers"""
```

---

## 5. Backend Implementation

### 5.1 Market Indicator Collector

**File:** `backend/app/collectors/market_indicator_collector.py`

> Library module — `training_data_builder`에서 import하여 사용.
> 하루에 1회만 API 호출, 결과 캐시하여 전 종목 공유.

```python
class MarketIndicatorCollector:
    """시장 지표 수집기. 일 1회 호출, 캐시."""

    TICKERS = {
        "kospi": "^KS11",
        "sp500": "^GSPC",
        "vix": "^VIX",
        "usd_krw": "KRW=X",
    }

    _cache: dict[str, dict] = {}  # date → indicators

    def fetch_daily_indicators(self, target_date: date, market: str) -> dict:
        """시장 지표 수집 (캐시 우선)."""
        # Returns: {"market_return": float, "vix_change": float,
        #           "usd_krw_change": float (KR only)}
        # market_return = KOSPI change (KR) or S&P500 change (US)

    def _fetch_with_retry(self, tickers, start, end, max_retries=3) -> pd.DataFrame:
        """yfinance 호출 + exponential backoff retry."""
        # Fallback: FinanceDataReader for KR data
```

### 5.2 Feature Configuration (Metadata Only)

**File:** `backend/app/processing/feature_config.py`

> Metadata-only module. 피처 계산 로직 없음. 이름과 그룹 정의만.

```python
TIER_1_FEATURES = [
    "news_score", "sentiment_score", "rsi_14",
    "prev_change_pct", "price_change_5d", "volume_change_5d",
    "market_return", "vix_change",
]

TIER_2_FEATURES = TIER_1_FEATURES + [
    "news_count_3d", "avg_score_3d", "sentiment_trend",
    "ma5_ratio", "volatility_5d",
    "usd_krw_change", "has_earnings_disclosure", "cross_theme_score",
]

TIER_3_FEATURES = TIER_2_FEATURES + [
    "foreign_net_ratio", "sector_index_change",
    "disclosure_ratio", "bb_position",
]

# 피처 제거됨 (사유 기록)
REMOVED_FEATURES = {
    "prev_close": "절대값, 방향 무관 (Fama & French 1993)",
    "prev_volume": "절대값, 종목 크기만 반영",
    "individual_net_buy": "선형 종속 (= -(foreign+institution))",
    "stochastic_k": "RSI와 중복 (r~0.6)",
    "stochastic_d": "RSI와 중복",
    "nasdaq_change": "S&P500과 r~0.9",
    "news_acceleration": "2차 도함수 = 노이즈 증폭",
    "news_velocity_1h": "1h 윈도우 극단적 노이즈",
    "days_to_month_end": "방향 무관 연속값",
    "atr_14": "volatility_5d와 중복 (r~0.7)",
    "ma60_ratio": "1일 예측에 너무 느림",
    "is_friday": "효과 미입증",
    "is_month_end": "효과 < 0.3%",
    "is_quarter_end": "연 4회, 학습 불가",
    "gold_change": "주식과 불안정 관계",
    "crude_oil_change": "에너지 섹터만 유효",
}

def get_features_for_tier(tier: int) -> list[str]:
    """주어진 Tier의 피처 목록 반환."""
    if tier == 1:
        return TIER_1_FEATURES
    elif tier == 2:
        return TIER_2_FEATURES
    elif tier == 3:
        return TIER_3_FEATURES
    raise ValueError(f"Invalid tier: {tier}")

def get_min_samples_for_tier(tier: int) -> int:
    """Tier별 최소 필요 샘플 수 (보수적 임계값).

    N/10 이론 최소값(80, 160, 200)보다 높은 실전 임계값 적용.
    TimeSeriesSplit CV 안정성 + 과적합 방지 목적.
    """
    thresholds = {1: 200, 2: 500, 3: 1000}
    return thresholds.get(tier, 200)
```

### 5.3 Feature Validator

**File:** `backend/app/processing/feature_validator.py`

```python
FEATURE_BOUNDS = {
    "rsi_14": (0, 100),
    "bb_position": (0, 1),
    "sentiment_score": (-1, 1),
    "news_score": (0, 100),
    "confidence": (0, 1),
    "volatility_5d": (0, 50),
}

class FeatureValidator:
    def validate(self, features: dict) -> dict:
        """Validate bounds, clip outliers, flag issues."""

    def impute_missing(self, features: dict, defaults: dict) -> dict:
        """Replace None with defaults (median or 0)."""

    def null_rate_report(self, db: Session, market: str) -> dict:
        """Report null rate per feature. Alert if > 30%."""
```

### 5.4 Cross-Theme Scorer

**File:** `backend/app/processing/cross_theme_scorer.py`

```python
def calc_cross_theme_score(
    db: Session, theme: str, stock_code: str, market: str, target_date: date
) -> float:
    """동일 테마 타 종목 평균 뉴스 스코어 (자기 자신 제외)."""
```

### 5.5 ML Training Pipeline

**File:** `backend/app/processing/ml_trainer.py`

```python
class MLTrainer:
    """LightGBM + RandomForest 학습 파이프라인."""

    def __init__(self, market: str, tier: int = 1):
        self.market = market
        self.tier = tier
        self.feature_columns = get_features_for_tier(tier)

    def load_training_data(self, db: Session) -> tuple[pd.DataFrame, pd.Series]:
        """DB에서 labeled data 로드. TimeSeriesSplit 준비."""

    def train_lightgbm(self, X, y) -> dict:
        """LightGBM 학습. Returns {accuracy, cv_accuracy, cv_std, model}."""

    def train_random_forest(self, X, y) -> dict:
        """RandomForest 학습. Returns same metrics."""

    def cross_validate(self, X, y, n_splits=5) -> dict:
        """TimeSeriesSplit CV. Never random split."""

    def save_model(self, db: Session, name: str, version: str) -> str:
        """Pickle + SHA-256 checksum + DB metadata."""
```

> **Data Leakage Prevention:** TimeSeriesSplit만 사용. Random split 금지.
> Train dates < validation dates < test dates 보장.

### 5.6 ML Model Evaluator

**File:** `backend/app/processing/ml_evaluator.py`

```python
class MLEvaluator:
    def evaluate(self, model, X_test, y_test) -> dict:
        """Returns {accuracy, precision, recall, f1, confusion_matrix}."""

    def compare_models(self, models: dict, X_test, y_test) -> pd.DataFrame:
        """여러 모델 비교. Best model 선정."""

    def ab_test_features(self, db, tier_a: int, tier_b: int) -> dict:
        """Tier A vs Tier B 정확도 비교 (paired test)."""

    def feature_importance(self, model, feature_names) -> list[dict]:
        """피처 중요도 분석. Returns sorted list."""
```

### 5.7 Model Registry

**File:** `backend/app/processing/model_registry.py`

```python
class ModelRegistry:
    def save(self, model, metadata: dict, db: Session) -> int:
        """Save model file + DB record. Returns model_id."""

    def load(self, model_id: int, db: Session):
        """Load model by ID. Verify checksum."""

    def activate(self, model_id: int, db: Session):
        """Set model as active (deactivate others)."""

    def get_active(self, market: str, db: Session):
        """Get currently active model for market."""
```

---

## 6. API Design

### 6.1 Endpoints

```
# Existing
GET  /api/v1/training/data       → Training data (paginated)
GET  /api/v1/training/export     → CSV download
GET  /api/v1/training/stats      → Statistics

# New
POST /api/v1/training/train      → Trigger model training
GET  /api/v1/training/models     → List trained models
GET  /api/v1/training/models/{id} → Model detail
POST /api/v1/training/models/{id}/activate → Activate model
GET  /api/v1/training/evaluate   → Evaluation report
POST /api/v1/training/predict    → Run prediction
GET  /api/v1/training/features   → Feature tiers info
```

### 6.2 Key Endpoint Specs

#### POST /api/v1/training/train

```json
// Request
{
    "market": "KR",
    "model_type": "lightgbm",
    "tier": 1,
    "test_ratio": 0.2
}
// Response
{
    "model_id": 1,
    "model_name": "lgbm_kr_t1_v1",
    "tier": 1,
    "feature_count": 8,
    "train_accuracy": 0.65,
    "test_accuracy": 0.61,
    "cv_accuracy": 0.59,
    "cv_std": 0.03,
    "train_samples": 160,
    "test_samples": 40,
    "top_features": [
        {"name": "rsi_14", "importance": 0.18},
        {"name": "news_score", "importance": 0.15}
    ]
}
```

#### GET /api/v1/training/features

```json
{
    "tiers": {
        "1": {
            "features": ["news_score", "sentiment_score", "rsi_14", "..."],
            "min_samples": 80,
            "status": "active"
        },
        "2": {
            "features": ["...+8 more"],
            "min_samples": 160,
            "status": "pending_data"
        },
        "3": {
            "features": ["...+4 more"],
            "min_samples": 200,
            "status": "pending_data"
        }
    },
    "removed": {"prev_close": "절대값, 방향 무관", "...": "..."},
    "current_samples": {"KR": 210, "US": 85}
}
```

---

## 7. Frontend Design

### 7.1 ML Dashboard Page (`/ml-dashboard`)

```
┌──────────────────────────────────────────────────┐
│ ML Model Dashboard                               │
├──────────────┬───────────────────────────────────┤
│ Active Model │  Accuracy Trend (Recharts Line)   │
│ ┌──────────┐ │  ┌───────────────────────────┐    │
│ │ LightGBM │ │  │ 65% ─── ──── ───          │    │
│ │ Tier 1   │ │  │ 60% ─── ──── ───          │    │
│ │ KR  61%  │ │  │ 55% ─── ──── ───          │    │
│ │ 8 feats  │ │  └───────────────────────────┘    │
│ └──────────┘ │                                    │
│              │  Feature Importance (BarChart)      │
│ Tier Status  │  ┌───────────────────────────┐    │
│ T1: Active   │  │ ████████ rsi_14     18%   │    │
│ T2: 300/500  │  │ ███████  news_score 15%   │    │
│ T3: Locked   │  │ ██████   vix_change 12%   │    │
│              │  │ █████    prev_chg   10%   │    │
│ [Train New]  │  └───────────────────────────┘    │
├──────────────┴───────────────────────────────────┤
│ Confusion Matrix    │  Direction Accuracy         │
│ ┌───┬────┬────┬───┐ │  ┌─────────────────────┐   │
│ │   │ UP │ DN │ N │ │  │ Up:   65% (42/65)   │   │
│ │UP │ 42 │  8 │15 │ │  │ Down: 62% (38/61)   │   │
│ │DN │ 10 │ 38 │13 │ │  │ Neut: 55% (28/51)   │   │
│ │N  │  9 │  7 │28 │ │  └─────────────────────┘   │
│ └───┴────┴────┴───┘ │                             │
└─────────────────────┴─────────────────────────────┘
```

### 7.2 Frontend Files

```
frontend/src/
├── pages/
│   └── MLDashboardPage.tsx          # NEW
├── components/ml/
│   ├── ModelCard.tsx                # NEW
│   ├── TierStatus.tsx              # NEW
│   ├── AccuracyTrendChart.tsx      # NEW
│   ├── FeatureImportanceChart.tsx   # NEW
│   ├── ConfusionMatrix.tsx         # NEW
│   └── DirectionAccuracy.tsx       # NEW
├── hooks/
│   └── useMLDashboard.ts           # NEW
├── api/
│   └── training.ts                 # MODIFY
└── types/
    └── training.ts                 # NEW
```

---

## 8. Verification & Quality

### 8.1 Model Validation Protocol

```
1. TimeSeriesSplit CV (5-fold): Accuracy + std 확인
2. Out-of-sample test: 최근 20% 데이터로 검증
3. Tier 승격 A/B test: Tier N+1 > Tier N + 2% 시 승격
4. 주간 모니터링: 7일 rolling accuracy 추적
5. 자동 알림: accuracy < 55% 시 경고
```

### 8.2 Data Quality Monitoring

| Metric | Threshold | Action |
|--------|-----------|--------|
| Feature null rate | > 30% | Alert + investigate |
| yfinance failure | > 20% | Fallback to FinanceDataReader |
| Accuracy (7d rolling) | < 55% | Alert + consider rollback |
| Feature importance drift | Top-3 change > 50% | Retrain |
| New data freshness | 3일 미수집 | Alert + check scheduler |

### 8.3 Rollback Strategy

```
1. Model rollback: API로 이전 버전 활성화
2. Tier rollback: feature_config에서 tier 낮춤
3. Schema rollback: Alembic downgrade (all nullable)
4. Data preserved: 제거 피처도 DB에는 잔존
```

---

## 9. Implementation Tasks

### Phase 0: Data Sprint (5 tasks) — PREREQUISITE

> 200+ labeled samples 확보 전까지 Phase 1 시작 불가.

| ID | Task | File | Priority |
|----|------|------|----------|
| P0-1 | Historical backfill script (30일 역산) | processing/training_backfill.py | CRITICAL |
| P0-2 | SQLite WAL mode 활성화 | core/database.py | CRITICAL |
| P0-3 | yfinance retry + FinanceDataReader fallback | collectors/yfinance_middleware.py | HIGH |
| P0-4 | Feature validator (bounds, null imputation) | processing/feature_validator.py | HIGH |
| P0-5 | Gate test: 200+ samples, baseline accuracy 확인 | tests/integration/test_data_readiness.py | CRITICAL |

### Phase 1: Tier 1 Model (10 tasks)

> 핵심 8개 피처로 LightGBM 학습. 기존 RF와 비교.

| ID | Task | File | Depends | Priority |
|----|------|------|---------|----------|
| P1-1 | market_indicator_collector (library module) | collectors/market_indicator_collector.py | P0-3 | HIGH |
| P1-2 | test_market_indicator_collector | tests/unit/test_market_indicator_collector.py | - | HIGH |
| P1-3 | feature_config module (tier definitions) | processing/feature_config.py | - | HIGH |
| P1-4 | test_feature_config | tests/unit/test_feature_config.py | P1-3 | HIGH |
| P1-5 | Extend training_data_builder (market_return, vix_change) | processing/training_data_builder.py | P1-1,P1-3 | HIGH |
| P1-6 | Alembic migration (Tier 1 columns) | alembic/versions/xxx_tier1.py | P1-5 | HIGH |
| P1-7 | ml_trainer (LightGBM + RF, TimeSeriesSplit) | processing/ml_trainer.py | P1-3 | HIGH |
| P1-8 | test_ml_trainer | tests/unit/test_ml_trainer.py | P1-7 | HIGH |
| P1-9 | ml_evaluator (compare, feature importance) | processing/ml_evaluator.py | P1-7 | HIGH |
| P1-10 | Integration test: Tier 1 full pipeline | tests/integration/test_tier1_pipeline.py | P1-5,P1-7 | HIGH |

### Phase 2: Tier 2 Expansion (10 tasks)

> +8개 피처를 배치별로 추가. 각 배치 A/B 검증.
> **Gate:** N >= 500 samples.

| ID | Task | File | Depends | Priority |
|----|------|------|---------|----------|
| P2-1 | DART collector enhancement (earnings flag) | collectors/dart_collector.py | - | MEDIUM |
| P2-2 | cross_theme_scorer module | processing/cross_theme_scorer.py | - | MEDIUM |
| P2-3 | test_cross_theme_scorer | tests/unit/test_cross_theme_scorer.py | P2-2 | MEDIUM |
| P2-4 | Extend training_data_builder (Tier 2 features) | processing/training_data_builder.py | P2-1,P2-2 | HIGH |
| P2-5 | Alembic migration (Tier 2 columns) | alembic/versions/xxx_tier2.py | P2-4 | HIGH |
| P2-6 | A/B test framework (tier comparison) | processing/ml_evaluator.py | P1-9 | HIGH |
| P2-7 | test_ab_test_framework | tests/unit/test_ml_evaluator.py | P2-6 | HIGH |
| P2-8 | Batch A/B validation: each Tier 2 batch | tests/integration/test_tier2_batches.py | P2-4,P2-6 | HIGH |
| P2-9 | model_registry module | processing/model_registry.py | P1-7 | MEDIUM |
| P2-10 | MLModel DB model + migration | models/ml_model.py | - | MEDIUM |

### Phase 3: Tier 3 + Frontend (10 tasks)

> **Gate:** N >= 1000 samples. KRX data는 OPTIONAL.

| ID | Task | File | Depends | Priority |
|----|------|------|---------|----------|
| P3-1 | KRX foreign_net_ratio collector (OPTIONAL) | collectors/krx_investor_collector.py | - | MEDIUM |
| P3-2 | Extend builder (Tier 3: foreign, sector) | processing/training_data_builder.py | P3-1 | MEDIUM |
| P3-3 | Alembic migration (Tier 3 columns) | alembic/versions/xxx_tier3.py | P3-2 | MEDIUM |
| P3-4 | Extend training API (train/models/predict/evaluate) | api/training.py | P2-9 | HIGH |
| P3-5 | test_training_api_extended | tests/integration/test_training_api_ext.py | P3-4 | HIGH |
| P3-6 | ML Dashboard page | frontend/src/pages/MLDashboardPage.tsx | P3-4 | HIGH |
| P3-7 | ML dashboard components | frontend/src/components/ml/*.tsx | P3-6 | HIGH |
| P3-8 | useMLDashboard hook + API client | frontend/src/hooks/useMLDashboard.ts | P3-4 | HIGH |
| P3-9 | Frontend types | frontend/src/types/training.ts | P3-4 | HIGH |
| P3-10 | Frontend tests (unit + E2E) | frontend/tests/ | P3-6 | HIGH |

### Phase 4: Optimization (4 tasks)

| ID | Task | File | Depends | Priority |
|----|------|------|---------|----------|
| P4-1 | Automated feature selection (SHAP) | processing/ml_trainer.py | P2-6 | MEDIUM |
| P4-2 | Hyperparameter tuning (Optuna) | processing/ml_trainer.py | P1-7 | LOW |
| P4-3 | Model auto-rollback (accuracy monitoring) | processing/model_registry.py | P2-9 | MEDIUM |
| P4-4 | Monitoring alerts (null rate, accuracy drop) | api/training.py | P3-4 | LOW |

### Task Summary

| Phase | Tasks | New Tests | New Files | Modified Files |
|-------|-------|-----------|-----------|----------------|
| Phase 0 | 5 | ~10 | 3 | 1 |
| Phase 1 | 10 | ~30 | 5 | 2 |
| Phase 2 | 10 | ~20 | 3 | 3 |
| Phase 3 | 10 | ~20 | 6 | 3 |
| Phase 4 | 4 | ~10 | 0 | 3 |
| **Total** | **39** | **~90** | **17** | **12** |

---

## 10. Execution Order

```
Week 1: Phase 0 + Phase 1 Start
  ├── Day 1: P0-1,P0-2,P0-3 (parallel: backfill + WAL + yfinance)
  ├── Day 2: P0-4, P1-1,P1-2 (validator + market collector)
  ├── Day 3: P1-3,P1-4,P1-5,P1-6 (feature config + builder + migration)
  ├── Day 4: P1-7,P1-8 (ml_trainer)
  └── Day 5: P1-9,P1-10 (evaluator + integration test)
  GATE: P0-5 must pass (200+ samples, baseline confirmed)

Week 2: Phase 2 (requires Gate)
  ├── Day 1-2: P2-1,P2-2,P2-3 (DART + cross_theme)
  ├── Day 2-3: P2-4,P2-5 (builder extension + migration)
  ├── Day 3-4: P2-6,P2-7,P2-8 (A/B framework + batch validation)
  └── Day 4-5: P2-9,P2-10 (model registry + MLModel)
  GATE: N >= 500 samples for Tier 2 activation

Week 3: Phase 3
  ├── Day 1: P3-1 (KRX — OPTIONAL, skip if unavailable)
  ├── Day 1-2: P3-2,P3-3,P3-4,P3-5 (builder + API)
  ├── Day 2-4: P3-6,P3-7,P3-8,P3-9 (frontend)
  └── Day 5: P3-10 (frontend tests)

Week 4+: Phase 4
  └── Ongoing: SHAP, Optuna, monitoring
```

---

## 11. Dependencies

### Python Packages

```
# New
lightgbm>=4.0.0           # Phase 1

# Phase 4 (optional)
optuna>=3.5.0              # Hyperparameter tuning
shap>=0.44.0               # Feature importance

# Existing
scikit-learn, yfinance, pandas, numpy
```

### KR Market Fallback

```
# If yfinance fails for KR data
FinanceDataReader>=0.9.0   # pykrx alternative for KR stocks
```

---

## 12. Resource Estimation

### API Calls

| Source | Calls/Day | Risk |
|--------|----------|------|
| yfinance (market indicators) | 4 (cached) | Rate limit |
| yfinance (stock prices) | 20-50 | Rate limit |
| DART API | 100-500 | Stable |

### Storage

| Period | Records | Size |
|--------|---------|------|
| 1 month | ~600 | ~1 MB |
| 1 year | ~7,200 | ~10 MB |

> SQLite → PostgreSQL migration trigger: 500+ records (Phase 2)

### Training Compute

| Operation | Duration |
|-----------|----------|
| LightGBM training (500 samples, 8 features) | ~3 sec |
| LightGBM training (1000 samples, 20 features) | ~10 sec |
| Optuna tuning (100 trials) | ~5 min |

---

## Appendix A: Feature Analysis Report

Full analysis at: `.omc/scientist/reports/20260220_feature_analysis.md`

> **Note:** Feature Analysis Report의 Tier 구성(학술적 중요도 순)과 본 Spec의 Tier 구성(데이터 가용성 순)은 다름.
> Report는 foreign_net_ratio를 Tier 1으로 분류했으나, KRX 데이터 확보 어려움으로 본 Spec에서는 Tier 3(OPTIONAL)으로 이동.
> 반면 prev_change_pct, price_change_5d, volume_change_5d는 이미 수집 중이므로 Report의 Tier 2에서 본 Spec의 Tier 1으로 승격.
> Report의 총 피처 수(T1:8, T2:19, Full:28)와 본 Spec(T1:8, T2:16, T3:20)이 다른 이유.

### Key Findings

1. **53개 피처는 200건 데이터에서 과적합 보장** (N/10 rule 위반)
2. **절대값(prev_close, prev_volume)은 방향 예측에 무의미** (Fama & French)
3. **RSI+Stochastic+MACD는 삼중 중복** (하나면 충분)
4. **캘린더 효과는 현대 시장에서 소멸** (Schwert 2003)
5. **외국인 순매수 비율은 KR 시장 최강 피처** (Kim & Wei 2002)
6. **뉴스 속도보다 뉴스 내용(sentiment)이 중요** (Tetlock 2007)
7. **Professional ceiling: 55-65%** (이 이상은 과적합 의심)

### Expected Performance

| Tier | Features | N Required | Accuracy |
|------|----------|-----------|----------|
| Tier 1 | 8 | 200+ | 58-62% |
| Tier 2 | 16 | 500+ | 60-65% |
| Tier 3 | 20 | 1000+ | 62-68% |

## Appendix B: Risk Matrix

| # | Risk | P | I | Mitigation |
|---|------|---|---|------------|
| 1 | Data scarcity | HIGH | CRITICAL | Phase 0 backfill |
| 2 | Overfitting | HIGH | HIGH | Tiered approach, N/10 rule |
| 3 | yfinance breakage | MED | HIGH | Retry + fallback |
| 4 | KRX unavailable | HIGH | MED | OPTIONAL, pykrx |
| 5 | Data leakage | MED | CRITICAL | TimeSeriesSplit only |
| 6 | Model corruption | LOW | HIGH | SHA-256 checksum |
| 7 | Feature null > 30% | LOW | MED | Validator + imputation |
| 8 | Accuracy plateau | MED | LOW | Accept professional ceiling |
