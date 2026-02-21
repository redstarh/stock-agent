# StockNews_Advan — 뉴스+공시 확률 예측 최적화 전략 문서

> **버전**: v1.0 (2026-02-21)
> **상태**: 구현 준비 완료 (Implementation-Ready)
> **목적**: 기존 StockNews 시스템의 예측 정확도를 향상시키는 독립 모듈 설계

---

## 목차

1. [개요](#1-개요)
2. [핵심 원리](#2-핵심-원리)
3. [기존 시스템 분석](#3-기존-시스템-분석)
4. [StockNews_Advan 아키텍처](#4-stocknews_advan-아키텍처)
5. [데이터 플로우](#5-데이터-플로우)
6. [구현 상세](#6-구현-상세)
7. [평가 지표](#7-평가-지표)
8. [정책 파라미터](#8-정책-파라미터)
9. [워크-포워드 시뮬레이션](#9-워크-포워드-시뮬레이션)
10. [구현 로드맵](#10-구현-로드맵)
11. [리스크 및 제한사항](#11-리스크-및-제한사항)

---

## 1. 개요

### 1.1 배경

현재 StockNews 시스템은 3단계 예측 파이프라인을 갖추고 있음:

1. **Heuristic 예측** — 뉴스 스코어 + 감성 점수 기반
2. **LLM 예측** — 과거 검증 데이터에서 생성된 컨텍스트 참고
3. **시뮬레이션** — 과거 데이터로 백테스트 (heuristic/llm/llm_custom_context)

**현재 한계**:
- 이벤트 유형별 차별화 없음 (DART 공시와 일반 뉴스를 동일하게 처리)
- 확률 예측이 아닌 분류(up/down/neutral)만 수행
- 정책 파라미터 자동 튜닝 없음
- 미래 정보 누수 방지 메커니즘 부족

### 1.2 StockNews_Advan의 목표

**"예측률을 올리는 것"**이 아니라 **"확률 예측 품질을 최적화하는 것"**

- **이벤트 구조화**: NewsEvent → AdvanEvent (이벤트 유형, 방향성, 규모, 신뢰도)
- **확률 출력**: P(up), P(down), P(flat) + 근거 + 불확실성
- **정책 자동 튜닝**: 이벤트별 priors, 결정 임계값, retrieval 정책
- **평가 지표**: Brier score, Calibration error, AUC
- **누수 방지**: 시간 컷오프 엄격 적용, 워크-포워드 시뮬레이션

### 1.3 기존 코드 재사용 원칙

**절대 변경하지 않는 것**:
- `backend/app/models/news_event.py` — NewsEvent 모델
- `backend/app/processing/llm_predictor.py` — 기존 LLM 예측기
- `backend/app/processing/simulation_engine.py` — 기존 시뮬레이션 엔진
- `backend/app/api/simulation.py` — 기존 시뮬레이션 API

**새로운 모듈 위치**:
- `backend/app/advan/` — 모든 Advan 관련 코드
- `frontend/src/pages/SimulationAdvanPage.tsx` — 전용 프론트엔드 페이지

---

## 2. 핵심 원리

### 2.1 Context를 "길게"가 아니라 "정확한 구조"로

LLM 성능은 정보의 양보다 **입력 구조(포맷)**와 **금지 규칙(누수 방지)**에서 결정됨.

**원칙**:
1. **미래 정보 누수 차단**: 공시/뉴스 시간과 예측 시점을 엄격히 고정
2. **구조화 요약**: 기사 원문이 아니라 이벤트 단위 구조화 데이터 제공
3. **이벤트 메타데이터**: 유형/방향성/규모/확률/근거/리스크/과거유사사례

### 2.2 목표를 "주가 맞추기"가 아니라 "조건부 확률 추정"으로

**출력 스키마**:
```json
{
  "prediction": "up|down|flat|abstain",
  "p_up": 0.45,
  "p_down": 0.25,
  "p_flat": 0.30,
  "confidence": 0.72,
  "top_drivers": [
    {
      "feature": "earnings_surprise",
      "sign": "positive",
      "weight": 0.8,
      "evidence": "영업이익 YoY +35%, 컨센서스 대비 +12%"
    }
  ],
  "invalidators": ["대규모 매도 공시", "섹터 전체 급락"],
  "trade_action": "buy|hold|skip",
  "position_size": 0.15
}
```

**평가 지표**: 단순 정확도보다 **Brier score** (확률 예측 품질), **AUC**, **Calibration** (신뢰도).

### 2.3 "DART+뉴스"는 이벤트 강도가 다르다 → 가중치 학습 필수

| 소스 | 이벤트 강도 | 신뢰도 | 예시 |
|------|-------------|--------|------|
| DART 공시 | **강함** | high | 실적, 증자, 소송, 공급계약, M&A |
| 언론 뉴스 | 약함 | medium-low | 추정 기사, 루머, 단독 보도 |
| SNS/커뮤니티 | 매우 약함 | low | 트위터, 네이버 카페 |

**해결책**: 이벤트별 **역사적 영향력 priors**를 Context에 주입.

### 2.4 반복 개선은 "프롬프트 수정"이 아니라 "정책(Policy) 업데이트"

**Policy란?**
- 이벤트 유형별 기대 영향 가중치
- 결정 임계값 (언제 매수/관망/유보하는지)
- Retrieval 정책 (어떤 과거 유사사례를 넣는지)
- 템플릿 (입력/출력 포맷)

**자동 탐색 방법**: Bayesian optimization / Multi-armed bandit / Evolutionary search

---

## 3. 기존 시스템 분석

### 3.1 기존 테이블 구조

#### NewsEvent (뉴스 원본)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| market | String(5) | KR/US |
| stock_code | String(20) | 종목코드 |
| stock_name | String(100) | 종목명 |
| title | String(500) | 뉴스 제목 |
| summary | String(2000) | 요약 |
| content | String(5000) | 본문 |
| sentiment | String(10) | positive/neutral/negative |
| sentiment_score | Float | -1.0 ~ 1.0 |
| news_score | Float | 0-100 (Recency 0.4 + Frequency 0.3 + Sentiment 0.2 + Disclosure 0.1) |
| source | String(50) | Naver/DART/Finnhub/NewsAPI |
| source_url | String(1000) | 원문 URL (unique) |
| theme | String(100) | 테마 분류 |
| kr_impact_themes | String(500) | 한국 시장 영향 테마 |
| is_disclosure | Boolean | DART 공시 여부 |
| published_at | DateTime(tz) | 발표 시각 |
| created_at | DateTime(tz) | DB 저장 시각 |

**Index**: `(market, stock_code)`, `published_at`

#### StockTrainingData (예측 시점 피처 스냅샷)

ML 학습용 데이터. 예측 시점의 모든 피처를 저장.

| 컬럼 그룹 | 주요 컬럼 |
|-----------|-----------|
| 기본 | prediction_date, stock_code, market |
| 뉴스 피처 | news_score, sentiment_score, news_count, news_count_3d, disclosure_ratio, sentiment_trend, theme |
| 주가 피처 | prev_close, prev_change_pct, ma5_ratio, ma20_ratio, volatility_5d, rsi_14, bb_position |
| 시장 피처 | market_index_change, vix_change, usd_krw_change, sector_index_change |
| 예측 결과 | predicted_direction, predicted_score, confidence |
| 실제 라벨 | actual_close, actual_change_pct, actual_direction, is_correct |

**Index**: `(prediction_date, stock_code)` unique, `(market, prediction_date)`

#### DailyPredictionResult (검증된 예측 결과)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| prediction_date | Date | 예측 날짜 |
| stock_code | String(20) | 종목코드 |
| market | String(5) | KR/US |
| predicted_direction | String(10) | up/down/neutral |
| predicted_score | Float | 0-100 |
| confidence | Float | 0.0-1.0 |
| news_count | Integer | 뉴스 건수 |
| actual_close | Float | 실제 종가 |
| actual_change_pct | Float | 실제 변화율 |
| actual_direction | String(10) | up/down/neutral |
| is_correct | Boolean | 예측 정확 여부 |

**Index**: `(prediction_date, stock_code)` unique

#### SimulationRun / SimulationResult (시뮬레이션 기록)

| 테이블 | 역할 |
|--------|------|
| SimulationRun | 시뮬레이션 실행 메타데이터 (method, date_from/to, accuracy_rate, context_id) |
| SimulationResult | 개별 종목 예측 결과 (run_id, stock_code, predicted/actual, is_correct) |
| SimulationContext | LLM 컨텍스트 버전 관리 (context_json, version, is_auto_generated) |

### 3.2 기존 프로세싱 로직

#### llm_predictor.py

```python
def predict_with_llm(
    db: Session,
    stock_code: str,
    market: str = "KR",
    context_path: str | None = None,
    target_date: date | None = None,
    context_dict: dict | None = None,
) -> LLMPredictionResponse
```

**플로우**:
1. Heuristic 예측 (baseline)
2. Context 로드 (파일 또는 딕셔너리)
3. 시스템 프롬프트 생성 (테마별 정확도, 감성 범위 분포, 실패 패턴)
4. 유저 메시지 생성 (종목 뉴스 데이터 + Heuristic 결과)
5. LLM 호출 (call_llm)
6. 응답 파싱 (JSON)
7. 실패 시 Heuristic fallback

**재사용**: 이 로직을 그대로 사용하되, Advan은 **더 구조화된 context_dict**를 제공.

#### prediction_context_builder.py

```python
def build_prediction_context(
    db: Session, days: int = 30, market: str | None = None
) -> dict
```

**생성 데이터**:
- `direction_accuracy`: 방향별 정확도
- `theme_predictability`: 테마별 예측 가능성
- `sentiment_ranges`: 감성 점수 범위별 실제 방향 분포
- `news_count_effect`: 뉴스 건수별 정확도
- `confidence_calibration`: Confidence 보정 분석
- `score_ranges`: 예측 점수 구간별 실제 방향 분포
- `failure_patterns`: 실패 패턴 (high_score_down, low_score_up, high_confidence_wrong)
- `market_conditions`: 시장별 조건 분석

**재사용**: 이 분석 결과를 **Policy priors 초기값**으로 활용.

#### simulation_engine.py

```python
def run_simulation(db: Session, config: SimulationRunCreate, run_id: int | None = None) -> SimulationRun
```

**플로우**:
1. 비즈니스일 목록 생성 (월-금)
2. 각 날짜별로 뉴스 있는 종목 조회
3. DailyPredictionResult에서 실제 데이터 조회 (검증된 것만)
4. 예측 실행 (heuristic / llm / llm_custom_context)
5. is_correct 계산
6. SimulationResult 저장
7. 집계 (accuracy_rate, total_stocks, correct_count)

**재사용**: 이 엔진을 그대로 사용하되, Advan은 **method="advan"**을 추가.

---

## 4. StockNews_Advan 아키텍처

### 4.1 모듈 위치

```
backend/app/advan/
├── __init__.py
├── models.py              # AdvanEvent, AdvanPolicy, AdvanRun, AdvanResult
├── schemas.py             # Pydantic 스키마
├── event_extractor.py     # NewsEvent → AdvanEvent 변환
├── policy_manager.py      # Policy 저장/로드/버전 관리
├── advan_predictor.py     # 확률 예측 엔진 (LLM 호출 + Policy 적용)
├── advan_simulator.py     # 워크-포워드 시뮬레이션
├── evaluator.py           # Brier, Calibration, AUC 계산
├── optimizer.py           # Policy 자동 튜닝 (Bayesian optimization)
└── api.py                 # FastAPI 엔드포인트
```

### 4.2 새 테이블 정의

#### advan_event (이벤트 구조화)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| news_event_id | Integer | FK → news_event.id |
| stock_code | String(20) | 종목코드 (denormalized) |
| market | String(5) | KR/US |
| event_type | String(50) | earnings/guidance/contract/capital_raise/lawsuit/regulation/recall/m&a/dividend/buyback |
| direction | String(20) | positive/negative/mixed/unknown |
| magnitude | Float | 규모 (0.0-1.0 normalized) |
| magnitude_raw | String(200) | 원본 규모 표현 (예: "매출 대비 15%", "영업이익 YoY +35%") |
| novelty | Float | 기존 기대 대비 새로움 (0.0-1.0) |
| credibility | Float | 신뢰도 (0.0-1.0, DART=1.0, 루머=0.3) |
| confounders | String(500) | 동일 시각의 시장 충격/섹터 이슈 (JSON) |
| extracted_at | DateTime(tz) | 추출 시각 |

**Index**: `news_event_id` unique, `(stock_code, event_type)`

#### advan_policy (정책 버전 관리)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| name | String(200) | 정책 이름 |
| version | String(50) | 버전 (예: "v1.2.3") |
| policy_json | Text | JSON string (priors, thresholds, retrieval_config, template_id) |
| parent_id | Integer | FK → advan_policy.id (nullable, 진화 추적) |
| train_date_from | Date | 학습 구간 시작 |
| train_date_to | Date | 학습 구간 종료 |
| val_accuracy | Float | 검증 구간 정확도 |
| val_brier | Float | 검증 구간 Brier score |
| val_calibration | Float | 검증 구간 Calibration error |
| is_active | Boolean | 활성 정책 여부 |
| notes | Text | 메모 |
| created_at | DateTime(tz) | 생성 시각 |

**Index**: `(name, version)` unique, `is_active`

#### advan_run (Advan 시뮬레이션 실행)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| name | String(200) | 실행 이름 |
| policy_id | Integer | FK → advan_policy.id |
| market | String(5) | KR/US |
| date_from | Date | 시작 날짜 |
| date_to | Date | 종료 날짜 |
| status | String(20) | pending/running/completed/failed |
| total_stocks | Integer | 총 종목 수 |
| correct_count | Integer | 정확 예측 수 |
| accuracy_rate | Float | 정확도 (%) |
| brier_score | Float | Brier score |
| calibration_error | Float | Calibration error |
| auc_score | Float | AUC |
| duration_seconds | Float | 실행 시간 (초) |
| error_message | Text | 에러 메시지 |
| created_at | DateTime(tz) | 생성 시각 |
| completed_at | DateTime(tz) | 완료 시각 |

**Index**: `policy_id`, `(market, status)`

#### advan_result (개별 예측 결과)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| run_id | Integer | FK → advan_run.id |
| prediction_date | Date | 예측 날짜 |
| stock_code | String(20) | 종목코드 |
| stock_name | String(100) | 종목명 |
| market | String(5) | KR/US |
| p_up | Float | P(상승) |
| p_down | Float | P(하락) |
| p_flat | Float | P(중립) |
| predicted_direction | String(10) | up/down/flat/abstain |
| confidence | Float | 신뢰도 (0.0-1.0) |
| reasoning | Text | 예측 근거 |
| trade_action | String(10) | buy/hold/skip |
| position_size | Float | 포지션 크기 (0.0-1.0) |
| actual_direction | String(10) | 실제 방향 |
| actual_change_pct | Float | 실제 변화율 |
| is_correct | Boolean | 정확 여부 |
| brier_score_sample | Float | 개별 Brier score |

**Index**: `run_id`, `(prediction_date, stock_code)`, `stock_code`

---

## 5. 데이터 플로우

### 5.1 이벤트 추출 (NewsEvent → AdvanEvent)

**입력**: NewsEvent 레코드 (뉴스 제목, 요약, is_disclosure, source)

**처리** (`event_extractor.py`):
1. **이벤트 유형 분류** (키워드 매칭 + LLM):
   - earnings: "실적", "영업이익", "순이익", "매출"
   - guidance: "가이던스", "전망", "목표가"
   - contract: "수주", "공급계약", "MOU"
   - capital_raise: "유상증자", "전환사채", "신주인수권"
   - lawsuit: "소송", "특허 침해", "배상"
   - regulation: "규제", "과징금", "제재"
   - m&a: "인수", "합병", "지분 취득"
   - dividend: "배당", "주당배당"
   - buyback: "자사주", "소각"
   - recall: "리콜", "회수"

2. **방향성 추출**:
   - positive: sentiment_score > 0.3
   - negative: sentiment_score < -0.3
   - mixed: -0.3 <= sentiment_score <= 0.3 and (긍정+부정 키워드 공존)
   - unknown: 기타

3. **규모 계산**:
   - earnings: `abs(영업이익 YoY%)` / 100
   - contract: `계약규모 / 시가총액` (추정)
   - capital_raise: `조달액 / 시가총액`
   - 기타: sentiment_score 절댓값

4. **novelty** (새로움):
   - 과거 7일 내 동일 event_type 뉴스가 없으면 1.0
   - 있으면 sentiment 변화폭에 비례 (0.5-0.8)

5. **credibility** (신뢰도):
   - is_disclosure=True → 1.0
   - source="Naver" and (title에 "단독" or "속보") → 0.8
   - source="Finnhub" → 0.7
   - 기타 → 0.5

**출력**: AdvanEvent 레코드

### 5.2 예측 실행 (Advan Predictor)

**입력**: stock_code, prediction_date, policy_id

**처리** (`advan_predictor.py`):
1. Policy 로드 (priors, thresholds, retrieval_config)
2. AdvanEvent 조회 (해당 종목 + prediction_date 이전)
3. 유사 이벤트 retrieval:
   - 동일 event_type
   - 규모 구간 ±20%
   - 과거 30일~180일 범위
   - 상위 3개 선택 (novelty * credibility 기준)
4. LLM 프롬프트 생성:
   - 시스템: Policy priors, 금지 규칙 (시간 누수, 확률 합=1)
   - 유저: 이벤트 구조화 데이터 + 유사 사례
5. LLM 호출 → JSON 파싱 (p_up, p_down, p_flat, reasoning)
6. 결정 로직:
   - `max(p_up, p_down, p_flat)` < abstain_threshold → "abstain"
   - p_up >= buy_threshold → "buy"
   - 기타 → "hold" or "skip"
7. Position size 계산: `confidence * magnitude * (1 - confounders_weight)`

**출력**: 확률 + 예측 방향 + trade_action + reasoning

### 5.3 시뮬레이션 실행 (Advan Simulator)

**입력**: AdvanRunCreate (policy_id, date_from, date_to, market)

**처리** (`advan_simulator.py`):
1. 비즈니스일 목록 생성
2. 각 날짜별:
   - 뉴스 있는 종목 조회
   - AdvanEvent 추출 (미추출 시 실행)
   - Advan 예측 실행
   - DailyPredictionResult에서 실제 데이터 조회
   - is_correct, brier_score_sample 계산
   - AdvanResult 저장
3. 집계:
   - accuracy_rate, brier_score (평균), calibration_error, auc_score
   - AdvanRun 업데이트

**출력**: AdvanRun (completed)

### 5.4 평가 (Evaluator)

**입력**: AdvanResult 목록

**계산** (`evaluator.py`):
1. **Brier Score**:
   ```python
   brier = mean([
       (p_up - (1 if actual=='up' else 0))**2 +
       (p_down - (1 if actual=='down' else 0))**2 +
       (p_flat - (1 if actual=='flat' else 0))**2
       for each prediction
   ])
   ```
   - 0.0 (완벽) ~ 2.0 (최악)
   - 0.2 이하: 우수, 0.3 이하: 양호, 0.5 이상: 개선 필요

2. **Calibration Error**:
   ```python
   # Confidence 구간별 (0.0-0.3, 0.3-0.6, 0.6-1.0)
   for each bin:
       expected_accuracy = mean(confidence in bin)
       observed_accuracy = mean(is_correct in bin)
       error += abs(expected_accuracy - observed_accuracy) * count_in_bin
   calibration_error = error / total_count
   ```
   - 0.0 (완벽 보정) ~ 1.0 (보정 안 됨)
   - 0.05 이하: 우수, 0.1 이하: 양호

3. **AUC-ROC**:
   - Binary classification (up vs not-up, down vs not-down)
   - 각각 AUC 계산 후 평균
   - 0.5 (랜덤) ~ 1.0 (완벽)
   - 0.65 이상: 실용적, 0.75 이상: 우수

4. **이벤트 타입별 성능 분해**:
   ```python
   for event_type in ["earnings", "contract", ...]:
       results_subset = [r for r in results if r.event_type == event_type]
       accuracy, brier, count = calculate(results_subset)
   ```

**출력**: 평가 메트릭 딕셔너리

---

## 6. 구현 상세

### 6.1 API 엔드포인트

**베이스**: `/api/v1/advan`

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/events` | AdvanEvent 목록 조회 (필터: stock_code, event_type, date_from/to) |
| GET | `/events/{event_id}` | AdvanEvent 상세 조회 |
| POST | `/events/extract` | NewsEvent → AdvanEvent 일괄 추출 (백그라운드) |
| GET | `/policies` | Policy 목록 조회 |
| POST | `/policies` | Policy 생성 |
| GET | `/policies/{policy_id}` | Policy 상세 조회 (policy_json 포함) |
| PUT | `/policies/{policy_id}` | Policy 수정 |
| POST | `/policies/{policy_id}/activate` | Policy 활성화 |
| GET | `/runs` | AdvanRun 목록 조회 |
| POST | `/runs` | Advan 시뮬레이션 시작 (백그라운드) |
| GET | `/runs/{run_id}` | AdvanRun 상세 + 결과 조회 |
| GET | `/runs/{run_id}/evaluate` | 평가 메트릭 계산 (Brier, Calibration, AUC, 이벤트별 분해) |
| DELETE | `/runs/{run_id}` | AdvanRun + 결과 삭제 |
| GET | `/compare` | 다중 Run 비교 (run_ids query) |
| POST | `/optimize` | Policy 자동 튜닝 시작 (백그라운드) |
| GET | `/optimize/status` | 튜닝 진행 상태 조회 |

### 6.2 프론트엔드 페이지

**경로**: `/simulation-advan`

**구성**: 4개 탭

#### Tab 1: 이벤트 추출 (Event Extraction)

- **필터**: 날짜 범위, 시장 (KR/US), event_type
- **테이블**: AdvanEvent 목록 (stock_code, event_type, direction, magnitude, credibility, extracted_at)
- **액션**: "일괄 추출" 버튼 → POST `/advan/events/extract` (백그라운드)
- **상태**: 진행률 표시 (WebSocket or polling)

#### Tab 2: 정책 관리 (Policy Management)

- **목록**: Policy 카드 (name, version, val_accuracy, val_brier, is_active)
- **생성**: JSON 에디터로 policy_json 직접 입력 or "기본 템플릿 사용"
- **편집**: 기존 Policy를 복사하여 수정 (parent_id 자동 설정)
- **활성화**: "활성화" 버튼 → POST `/advan/policies/{id}/activate`
- **상세**: Policy JSON 뷰어 (priors, thresholds, retrieval_config)

#### Tab 3: 시뮬레이션 실행 (Simulation)

- **설정**: name, policy 선택, market, date_from/to
- **시작**: POST `/advan/runs` → 백그라운드 실행
- **목록**: AdvanRun 테이블 (name, policy, accuracy_rate, brier_score, status, created_at)
- **상세**: 클릭 시 모달 또는 서브페이지
  - Run 메타데이터
  - 평가 메트릭 (Accuracy, Brier, Calibration, AUC)
  - 방향별 정확도 차트 (up/down/flat)
  - 이벤트 타입별 성능 분해 테이블
  - 개별 결과 테이블 (stock_code, prediction_date, p_up/down/flat, actual, is_correct)

#### Tab 4: 정책 최적화 (Policy Optimization)

- **설정**: 기준 Policy, 학습 구간, 검증 구간, 탐색 전략 (Bayesian/Random/Grid)
- **파라미터 범위**:
  - priors: {event_type: [0.5-1.5]} (각 이벤트 유형별 가중치)
  - buy_threshold: [0.5-0.8]
  - abstain_threshold: [0.3-0.5]
  - retrieval_top_k: [1-5]
- **시작**: POST `/advan/optimize` → 백그라운드 실행
- **진행**: 진행률, 현재 best Policy, iteration history (Brier score curve)
- **완료**: 생성된 Policy 목록 (val_brier 순 정렬), "활성화" 버튼

### 6.3 Policy JSON 스키마

```json
{
  "priors": {
    "earnings": {"weight": 1.2, "confidence_boost": 0.1, "notes": "실적 서프라이즈는 강한 신호"},
    "contract": {"weight": 1.0, "confidence_boost": 0.05},
    "capital_raise": {"weight": 0.8, "confidence_boost": -0.1, "notes": "유상증자는 보통 부정적"},
    "lawsuit": {"weight": 0.6, "confidence_boost": 0.0},
    "regulation": {"weight": 0.7, "confidence_boost": 0.0},
    "m&a": {"weight": 1.1, "confidence_boost": 0.1},
    "dividend": {"weight": 0.5, "confidence_boost": 0.0},
    "buyback": {"weight": 0.9, "confidence_boost": 0.05},
    "recall": {"weight": 0.8, "confidence_boost": 0.0},
    "guidance": {"weight": 0.7, "confidence_boost": 0.0}
  },
  "thresholds": {
    "buy_p_up": 0.6,
    "buy_p_down": 0.6,
    "abstain_band": 0.4,
    "min_confidence": 0.5
  },
  "retrieval": {
    "top_k": 3,
    "min_days_ago": 30,
    "max_days_ago": 180,
    "similarity_method": "event_type_and_magnitude"
  },
  "template_id": "default_v1",
  "rules": {
    "time_leakage_prevention": true,
    "probability_sum_check": true,
    "allow_abstain": true
  }
}
```

---

## 7. 평가 지표

### 7.1 Brier Score (확률 예측 품질)

**정의**:
```
BS = (1/N) * Σ [(p_up - y_up)² + (p_down - y_down)² + (p_flat - y_flat)²]
```
- `y_up = 1` if actual="up", else 0
- 범위: 0.0 (완벽) ~ 2.0 (최악)

**해석**:
- 0.0-0.2: 우수 (엔터프라이즈급)
- 0.2-0.3: 양호 (실전 적용 가능)
- 0.3-0.5: 개선 필요
- 0.5+: 랜덤보다 나쁨

### 7.2 Calibration Error (신뢰도 보정)

**정의**:
```
CE = Σ |Expected_Accuracy - Observed_Accuracy| * (Count_in_Bin / Total)
```

**Bin 구간**:
- Low: 0.0-0.4
- Medium: 0.4-0.7
- High: 0.7-1.0

**예시**:
- Confidence 0.8 구간: 예측 100건 중 85건 정확 → 보정 잘됨
- Confidence 0.5 구간: 예측 100건 중 30건 정확 → 과신(overconfidence)

**해석**:
- 0.0-0.05: 우수
- 0.05-0.1: 양호
- 0.1+: 보정 필요

### 7.3 AUC-ROC (분류 품질)

**계산**:
1. Binary up vs not-up: AUC(p_up, y_up)
2. Binary down vs not-down: AUC(p_down, y_down)
3. 평균: (AUC_up + AUC_down) / 2

**해석**:
- 0.75+: 우수
- 0.65-0.75: 실용적
- 0.5-0.65: 약함
- 0.5: 랜덤

### 7.4 방향별 정확도 (Direction Accuracy)

**계산**:
```python
for direction in ["up", "down", "flat"]:
    total = count(predicted_direction == direction)
    correct = count(predicted_direction == direction and is_correct)
    accuracy = correct / total
```

**주의**: 단순 정확도는 클래스 불균형에 취약 → Brier/AUC를 주 지표로.

### 7.5 이벤트 타입별 성능 분해

**테이블 예시**:

| Event Type | Count | Accuracy | Brier | AUC |
|------------|-------|----------|-------|-----|
| earnings | 120 | 68.3% | 0.24 | 0.71 |
| contract | 45 | 55.6% | 0.38 | 0.58 |
| capital_raise | 30 | 63.3% | 0.28 | 0.65 |
| m&a | 25 | 72.0% | 0.21 | 0.76 |
| lawsuit | 18 | 50.0% | 0.45 | 0.52 |

**활용**: Prior 가중치 조정 (lawsuit는 낮추고, earnings/m&a는 높임)

---

## 8. 정책 파라미터

### 8.1 Priors (이벤트별 가중치)

**의미**: 이벤트 유형이 주가에 미치는 역사적 영향력.

**기본값** (경험적):
- earnings: 1.2 (실적은 강한 신호)
- contract: 1.0 (공급계약은 중립)
- capital_raise: 0.8 (유상증자는 보통 부정적)
- m&a: 1.1 (M&A는 긍정적)
- lawsuit: 0.6 (소송은 약한 신호)
- regulation: 0.7
- dividend: 0.5 (배당은 약함)
- buyback: 0.9 (자사주 소각은 긍정적)
- recall: 0.8
- guidance: 0.7

**튜닝 범위**: 0.5 ~ 1.5

### 8.2 Thresholds (결정 임계값)

| 파라미터 | 의미 | 기본값 | 범위 |
|----------|------|--------|------|
| buy_p_up | P(up) >= 이 값이면 매수 | 0.6 | 0.5-0.8 |
| buy_p_down | P(down) >= 이 값이면 매도/공매도 | 0.6 | 0.5-0.8 |
| abstain_band | max(p_up, p_down, p_flat) < 이 값이면 유보 | 0.4 | 0.3-0.5 |
| min_confidence | 최소 신뢰도 (이하 skip) | 0.5 | 0.3-0.7 |

### 8.3 Retrieval Config (유사 이벤트 검색)

| 파라미터 | 의미 | 기본값 | 범위 |
|----------|------|--------|------|
| top_k | 최대 검색 개수 | 3 | 1-5 |
| min_days_ago | 최소 과거 일수 | 30 | 7-60 |
| max_days_ago | 최대 과거 일수 | 180 | 90-365 |
| similarity_method | 유사도 계산 방식 | "event_type_and_magnitude" | 고정 |

**유사도 점수**:
```python
similarity = (
    (event_type_match ? 0.5 : 0.0) +
    (1.0 - abs(magnitude_diff) / 1.0) * 0.3 +
    novelty * 0.1 +
    credibility * 0.1
)
```

### 8.4 Rules (규칙)

| 규칙 | 설명 |
|------|------|
| time_leakage_prevention | 예측 시점 이후 데이터 사용 금지 (엄격 적용) |
| probability_sum_check | p_up + p_down + p_flat = 1.0 검증 |
| allow_abstain | 불확실 시 abstain 허용 |

---

## 9. 워크-포워드 시뮬레이션

### 9.1 데이터 분할

```
[======== 전체 데이터 ========]
[== Train ==][= Val =][= Test =]
 2024-01-01  2024-11-01 2025-01-01
             2024-12-31 2026-02-21
```

- **Train**: Policy optimizer가 학습 (priors, thresholds 탐색)
- **Val**: Policy 선택 (여러 후보 중 best 선택)
- **Test**: 최종 평가 (optimizer는 이 구간을 보지 못함)

### 9.2 시간 누수 방지

**원칙**:
1. 예측 시점 = prediction_date 23:59:59 (장 마감 후)
2. NewsEvent는 `published_at <= prediction_date 23:59:59`만 사용
3. AdvanEvent는 `extracted_at <= prediction_date 23:59:59`만 사용
4. 유사 이벤트 retrieval: `prediction_date - max_days_ago` ~ `prediction_date - min_days_ago` 범위
5. 실제 라벨은 `prediction_date + 1` (다음 영업일) 종가로 계산

**검증 코드**:
```python
def verify_no_leakage(prediction_date: date, events: list[AdvanEvent]) -> bool:
    cutoff = datetime.combine(prediction_date, datetime.max.time())
    for event in events:
        if event.extracted_at > cutoff:
            raise ValueError(f"Time leakage: event {event.id} extracted after prediction_date")
    return True
```

### 9.3 워크-포워드 프로토콜

**1일 단위로 앞으로 이동하며 예측**:

```
Day 1 (2024-01-02):
  - 사용 데이터: 2024-01-02 23:59:59 이전 뉴스
  - 예측 실행: stock_code별 확률 예측
  - 라벨링: 2024-01-03 종가로 actual_direction 계산
  - 평가: is_correct, brier_score_sample 계산

Day 2 (2024-01-03):
  - 사용 데이터: 2024-01-03 23:59:59 이전 뉴스 (Day 1 뉴스 포함)
  - 예측 실행
  - ...
```

**장점**: 과거 데이터에 대한 과최적화 방지, 실전 재현.

### 9.4 라벨링 규칙

**실제 변화율**:
```python
actual_change_pct = ((actual_close - prev_close) / prev_close) * 100
```

**방향 분류**:
```python
if actual_change_pct >= +2.0:
    actual_direction = "up"
elif actual_change_pct <= -2.0:
    actual_direction = "down"
else:
    actual_direction = "flat"
```

**초과 수익 옵션** (선택적):
```python
# 시장/섹터 수익률 제거
market_return = (market_index_close - market_index_prev) / market_index_prev * 100
excess_return = actual_change_pct - market_return

if excess_return >= +2.0:
    actual_direction = "up"
elif excess_return <= -2.0:
    actual_direction = "down"
else:
    actual_direction = "flat"
```

---

## 10. 구현 로드맵

### Phase 1: 기본 인프라 (1-2주)

- [ ] 테이블 생성 (advan_event, advan_policy, advan_run, advan_result)
- [ ] Alembic 마이그레이션 스크립트
- [ ] 모델 정의 (`backend/app/advan/models.py`)
- [ ] Pydantic 스키마 (`backend/app/advan/schemas.py`)
- [ ] API 라우터 등록 (`backend/app/advan/api.py` → `backend/app/api/v2/router.py`에 include)

**검증**: 테이블 생성 확인, API 엔드포인트 `/advan/health` 응답 확인

### Phase 2: 이벤트 추출 (1주)

- [ ] Event Extractor 구현 (`event_extractor.py`)
  - [ ] 이벤트 유형 분류 (키워드 매칭)
  - [ ] 방향성 추출 (sentiment_score 기반)
  - [ ] 규모 계산 (정규화)
  - [ ] novelty, credibility 계산
- [ ] API 엔드포인트: POST `/advan/events/extract` (백그라운드)
- [ ] 단위 테스트: NewsEvent 샘플 → AdvanEvent 변환

**검증**: 100개 NewsEvent → AdvanEvent 추출, event_type 분포 확인

### Phase 3: Policy Manager (1주)

- [ ] Policy Manager 구현 (`policy_manager.py`)
  - [ ] Policy CRUD (생성, 조회, 수정, 활성화)
  - [ ] 기본 Policy 템플릿 (priors, thresholds)
  - [ ] JSON 검증 (Pydantic)
- [ ] API 엔드포인트: GET/POST/PUT `/advan/policies`
- [ ] 프론트엔드 Tab 2: Policy Management 페이지

**검증**: 기본 Policy 생성, JSON 에디터로 수정, 활성화 토글

### Phase 4: Advan Predictor (2주)

- [ ] Advan Predictor 구현 (`advan_predictor.py`)
  - [ ] Policy 로드
  - [ ] AdvanEvent 조회
  - [ ] 유사 이벤트 retrieval
  - [ ] LLM 프롬프트 생성 (구조화)
  - [ ] LLM 호출 (`call_llm` 재사용)
  - [ ] 확률 파싱 (p_up, p_down, p_flat)
  - [ ] 결정 로직 (trade_action, position_size)
- [ ] 단위 테스트: 종목 1개 예측, 확률 합=1 검증

**검증**: 종목 5개 예측, p_up+p_down+p_flat=1.0, reasoning 출력 확인

### Phase 5: Advan Simulator (2주)

- [ ] Advan Simulator 구현 (`advan_simulator.py`)
  - [ ] 비즈니스일 목록 생성 (재사용)
  - [ ] 날짜별 종목 조회
  - [ ] 예측 실행 (Advan Predictor 호출)
  - [ ] 실제 데이터 조회 (DailyPredictionResult 재사용)
  - [ ] is_correct, brier_score_sample 계산
  - [ ] AdvanResult 저장
  - [ ] 집계 (accuracy_rate, brier_score, calibration_error, auc_score)
- [ ] API 엔드포인트: POST `/advan/runs` (백그라운드)
- [ ] 프론트엔드 Tab 3: Simulation 페이지

**검증**: 7일 시뮬레이션 실행, AdvanResult 100건 생성, Brier score < 0.5

### Phase 6: Evaluator (1주)

- [ ] Evaluator 구현 (`evaluator.py`)
  - [ ] Brier score 계산
  - [ ] Calibration error 계산 (bin 분할)
  - [ ] AUC-ROC 계산 (sklearn.metrics.roc_auc_score)
  - [ ] 이벤트 타입별 성능 분해
  - [ ] 방향별 정확도 계산
- [ ] API 엔드포인트: GET `/advan/runs/{id}/evaluate`
- [ ] 프론트엔드: 평가 메트릭 차트 (Recharts)

**검증**: 시뮬레이션 결과에 대해 Brier/Calibration/AUC 계산, 이벤트별 테이블 출력

### Phase 7: Policy Optimizer (2-3주)

- [ ] Optimizer 구현 (`optimizer.py`)
  - [ ] Bayesian Optimization (scikit-optimize)
  - [ ] 파라미터 범위 정의 (priors, thresholds)
  - [ ] 목적 함수: minimize(val_brier) or maximize(val_auc)
  - [ ] N iterations 실행 (각 iteration마다 Policy variant 생성 → 시뮬레이션 → 평가)
  - [ ] Best Policy 선택 (val_brier 최소)
  - [ ] 진행 상태 저장 (Redis or DB)
- [ ] API 엔드포인트: POST `/advan/optimize`, GET `/advan/optimize/status`
- [ ] 프론트엔드 Tab 4: Policy Optimization 페이지

**검증**: 10 iterations 실행, best Policy val_brier < baseline Policy, Policy 자동 생성 확인

### Phase 8: 프론트엔드 통합 (1주)

- [ ] SimulationAdvanPage 구현 (`frontend/src/pages/SimulationAdvanPage.tsx`)
- [ ] 4개 탭 구성 (Tabs 컴포넌트)
- [ ] API 클라이언트 (`frontend/src/api/advan.ts`)
- [ ] React Query hooks (`frontend/src/hooks/useAdvan*.ts`)
- [ ] 차트 컴포넌트 (Recharts)
- [ ] 테이블 컴포넌트 (TanStack Table)

**검증**: 브라우저에서 4개 탭 전환, CRUD 동작 확인

### Phase 9: 테스트 및 문서화 (1주)

- [ ] 단위 테스트 (pytest)
  - [ ] event_extractor
  - [ ] advan_predictor
  - [ ] evaluator
  - [ ] optimizer
- [ ] 통합 테스트
  - [ ] API 엔드포인트 (전체 플로우)
- [ ] E2E 테스트 (Playwright)
  - [ ] 시뮬레이션 생성 → 결과 조회
- [ ] API 문서 (Swagger)
- [ ] 사용자 가이드 (docs/Advan_User_Guide.md)

**검증**: 테스트 커버리지 80% 이상, E2E 시나리오 통과

### Phase 10: 배포 및 모니터링 (1주)

- [ ] Docker 이미지 빌드 (backend + frontend)
- [ ] 환경 변수 설정 (ADVAN_ENABLED=true)
- [ ] DB 마이그레이션 실행 (production)
- [ ] 모니터링 설정 (Prometheus + Grafana)
  - [ ] Advan 예측 latency
  - [ ] Brier score 추이
  - [ ] Policy 활성화 이벤트
- [ ] 알림 규칙 (Brier > 0.5, Calibration error > 0.15)

**검증**: Production 배포, 실시간 예측 동작 확인, 메트릭 수집 확인

---

## 11. 리스크 및 제한사항

### 11.1 데이터 품질 의존성

**리스크**: NewsEvent의 sentiment_score, theme 분류가 부정확하면 AdvanEvent 품질 저하.

**완화책**:
- Event Extractor에 LLM 검증 단계 추가 (샘플링)
- 수동 레이블링 데이터로 Extractor 튜닝
- credibility 가중치로 불확실한 이벤트 하향 조정

### 11.2 LLM 비용 및 Latency

**리스크**: 종목당 LLM 호출 → 비용 증가, 응답 속도 저하.

**완화책**:
- Advan은 고신뢰 종목만 예측 (news_score >= 60)
- Batch 예측 (비동기 처리)
- 캐싱 (동일 날짜 + 종목은 24시간 캐시)
- Local LLM 옵션 (Llama 3, Qwen)

### 11.3 과최적화 (Overfitting)

**리스크**: Policy optimizer가 train 구간에 과적합 → test 성능 저하.

**완화책**:
- Train/Val/Test 엄격 분리
- Holdout set (최신 30일)은 최종 평가 전까지 봉인
- Early stopping (val_brier 개선 없으면 중단)
- Regularization (priors 변화폭 제한)

### 11.4 시장 체제 변화 (Regime Change)

**리스크**: 과거 학습된 Policy가 새로운 시장 국면에서 무효.

**완화책**:
- 월 1회 Policy 재학습 (Rolling window)
- 시장 국면 감지 (VIX, 변동성 급증 시 Policy 중단)
- 앙상블 Policy (여러 Policy의 가중 평균)

### 11.5 Black Swan Events

**리스크**: COVID-19, 전쟁 등 극단 이벤트는 과거 데이터에 없음.

**완화책**:
- Abstain 적극 활용 (불확실하면 예측 유보)
- 컨파운더 감지 (시장 전체 급락 시 개별 종목 예측 중단)
- 인간 개입 (실시간 모니터링, 수동 Policy 비활성화)

### 11.6 규제 및 윤리

**리스크**: AI 기반 투자 조언 규제, 설명 가능성 요구.

**완화책**:
- reasoning 필드에 근거 명시 (투명성)
- 면책 조항 (이 시스템은 투자 조언이 아님, 참고 자료)
- 사용자 동의 (리스크 고지)

### 11.7 테스트 커버리지 부족

**리스크**: 예측 오류가 프로덕션에서 발견.

**완화책**:
- Phase 9 테스트 강화
- Staging 환경에서 1개월 검증 후 production 배포
- 점진적 롤아웃 (KR 시장 먼저 → US 시장)

### 11.8 프론트엔드 복잡도

**리스크**: 4탭 페이지가 무거워질 수 있음.

**완화책**:
- Code splitting (React.lazy)
- Virtualization (대용량 테이블)
- API pagination (limit=100)

---

## 12. 기대 효과

### 12.1 정량적 목표

| 메트릭 | 현재 (기존 LLM) | 목표 (Advan) | 개선율 |
|--------|-----------------|--------------|--------|
| Accuracy | 58% | 65% | +7%p |
| Brier Score | 0.35 | 0.25 | -28% |
| Calibration Error | 0.12 | 0.08 | -33% |
| AUC | 0.62 | 0.72 | +16% |
| Abstain Rate | 0% | 15% | - |

**핵심**: 단순 정확도보다 **확률 품질 향상** + **불확실 구간 유보**로 실전 수익률 향상.

### 12.2 정성적 효과

- **투명성**: reasoning 필드로 예측 근거 제공 → 사용자 신뢰 증가
- **적응성**: Policy 자동 튜닝 → 시장 변화에 대응
- **확장성**: 이벤트 유형 추가 용이 (priors만 추가)
- **독립성**: 기존 시스템과 분리 → 리스크 최소화

---

## 13. 결론

StockNews_Advan은 **기존 시스템을 대체하는 것이 아니라 보완하는 독립 모듈**입니다.

**핵심 차별점**:
1. 이벤트 구조화 (NewsEvent → AdvanEvent)
2. 확률 예측 (P(up), P(down), P(flat))
3. 정책 자동 튜닝 (Bayesian optimization)
4. 평가 지표 강화 (Brier, Calibration, AUC)
5. 시간 누수 방지 (워크-포워드 시뮬레이션)

**구현 원칙**:
- 기존 코드 변경 최소화 (NewsEvent, llm_predictor, simulation_engine 재사용)
- 독립 모듈 (`backend/app/advan/`)
- 단계적 배포 (Phase 1-10)

**예상 기간**: 10-12주 (2.5-3개월)

**다음 단계**: Phase 1 (기본 인프라) 시작 → Alembic 마이그레이션 생성.
