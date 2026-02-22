"""워크-포워드 시뮬레이터/백테스터.

이벤트 추출 → LLM 예측 → 라벨 생성 → 평가 루프.
기존 simulation_engine과 독립적으로 운영.
"""

import json
import logging
import time
from datetime import UTC, date, datetime, timedelta

from sqlalchemy.orm import Session

from app.advan.models import (
    AdvanEvent,
    AdvanFeatureDaily,
    AdvanLabel,
    AdvanPolicy,
    AdvanPrediction,
    AdvanSimulationRun,
)

logger = logging.getLogger(__name__)


def _get_business_days(start: date, end: date) -> list[date]:
    """영업일(월~금)만 반환."""
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:  # Mon=0 ~ Fri=4
            days.append(current)
        current += timedelta(days=1)
    return days


def _get_events_for_date(
    db: Session, market: str, target_date: date
) -> dict[str, list[AdvanEvent]]:
    """특정 날짜의 종목별 이벤트 조회.

    장전(전일 장마감 후 ~ 당일 장전) 이벤트만 포함.
    미래 누수 방지: target_date 이전 이벤트만.
    """
    # 더 넓은 범위: 최근 3일간 이벤트 (컨텍스트 제공)
    lookback = datetime.combine(target_date - timedelta(days=3), datetime.min.time())

    events = (
        db.query(AdvanEvent)
        .filter(
            AdvanEvent.market == market,
            AdvanEvent.event_timestamp >= lookback,
            AdvanEvent.event_timestamp < datetime.combine(target_date, datetime.min.time().replace(hour=15, minute=30)),
        )
        .order_by(AdvanEvent.event_timestamp.desc())
        .all()
    )

    # 종목별 그룹핑
    by_ticker: dict[str, list[AdvanEvent]] = {}
    for evt in events:
        if evt.ticker not in by_ticker:
            by_ticker[evt.ticker] = []
        by_ticker[evt.ticker].append(evt)

    return by_ticker


def _load_policy_params(policy: AdvanPolicy) -> dict:
    """정책 DB 레코드에서 파라미터 dict 로드."""
    return {
        "event_priors": json.loads(policy.event_priors) if policy.event_priors else {},
        "thresholds": json.loads(policy.thresholds) if policy.thresholds else {},
        "template_config": json.loads(policy.template_config) if policy.template_config else {},
        "retrieval_config": json.loads(policy.retrieval_config) if policy.retrieval_config else {},
    }


def _generate_label(
    db: Session,
    prediction: AdvanPrediction,
    label_threshold_pct: float,
) -> AdvanLabel | None:
    """예측에 대한 실현 수익률 라벨 생성.

    T+horizon 거래일의 종가 기준으로 라벨 산출.
    """
    target_date = prediction.prediction_date
    horizon = prediction.horizon

    # T+horizon 영업일 계산
    label_date = target_date
    biz_days_counted = 0
    current = target_date + timedelta(days=1)
    while biz_days_counted < horizon:
        if current.weekday() < 5:
            biz_days_counted += 1
            label_date = current
        current += timedelta(days=1)

    # 피처 데이터에서 수익률 조회
    base_feature = (
        db.query(AdvanFeatureDaily)
        .filter(
            AdvanFeatureDaily.ticker == prediction.ticker,
            AdvanFeatureDaily.trade_date == target_date,
        )
        .first()
    )

    target_feature = (
        db.query(AdvanFeatureDaily)
        .filter(
            AdvanFeatureDaily.ticker == prediction.ticker,
            AdvanFeatureDaily.trade_date == label_date,
        )
        .first()
    )

    if not base_feature or not target_feature:
        # 피처 없으면 기존 DailyPredictionResult에서 시도
        return _generate_label_from_verification(db, prediction, label_threshold_pct, label_date)

    if not base_feature.close_price or not target_feature.close_price:
        return None

    realized_ret = ((target_feature.close_price - base_feature.close_price) / base_feature.close_price) * 100

    # 초과수익률 (시장 수익률 제거)
    excess_ret = realized_ret
    if base_feature.market_ret is not None and target_feature.market_ret is not None:
        market_ret_period = target_feature.market_ret - base_feature.market_ret
        excess_ret = realized_ret - market_ret_period

    # 라벨 결정
    if realized_ret > label_threshold_pct:
        label = "Up"
    elif realized_ret < -label_threshold_pct:
        label = "Down"
    else:
        label = "Flat"

    # 예측 정확도 판정
    is_correct = None
    if prediction.prediction != "Abstain":
        is_correct = prediction.prediction == label

    advan_label = AdvanLabel(
        prediction_id=prediction.id,
        ticker=prediction.ticker,
        prediction_date=prediction.prediction_date,
        horizon=prediction.horizon,
        realized_ret=round(realized_ret, 4),
        excess_ret=round(excess_ret, 4),
        label=label,
        is_correct=is_correct,
        label_date=label_date,
    )

    return advan_label


def _generate_label_from_verification(
    db: Session,
    prediction: AdvanPrediction,
    label_threshold_pct: float,
    label_date: date,
) -> AdvanLabel | None:
    """기존 DailyPredictionResult에서 실제 데이터 조회하여 라벨 생성."""
    try:
        from app.models.verification import DailyPredictionResult

        result = (
            db.query(DailyPredictionResult)
            .filter(
                DailyPredictionResult.stock_code == prediction.ticker,
                DailyPredictionResult.prediction_date == prediction.prediction_date,
            )
            .first()
        )

        if not result or result.actual_direction is None:
            return None

        realized_ret = result.actual_change_pct if result.actual_change_pct is not None else 0.0

        if realized_ret > label_threshold_pct:
            label = "Up"
        elif realized_ret < -label_threshold_pct:
            label = "Down"
        else:
            label = "Flat"

        is_correct = None
        if prediction.prediction != "Abstain":
            is_correct = prediction.prediction == label

        return AdvanLabel(
            prediction_id=prediction.id,
            ticker=prediction.ticker,
            prediction_date=prediction.prediction_date,
            horizon=prediction.horizon,
            realized_ret=round(realized_ret, 4),
            excess_ret=None,
            label=label,
            is_correct=is_correct,
            label_date=label_date,
        )
    except Exception as e:
        logger.debug("Verification data lookup failed: %s", e)
        return None


def run_simulation(
    db: Session,
    run_id: int,
) -> None:
    """시뮬레이션 실행 (백그라운드 태스크).

    1. 기간 내 영업일 순회
    2. 종목별 이벤트 조회
    3. LLM/규칙 예측
    4. 라벨 생성
    5. 집계 메트릭 업데이트
    """
    start_time = time.time()

    run = db.query(AdvanSimulationRun).filter(AdvanSimulationRun.id == run_id).first()
    if not run:
        logger.error("Simulation run %d not found", run_id)
        return

    # 상태 업데이트
    run.status = "running"
    db.commit()

    try:
        policy = db.query(AdvanPolicy).filter(AdvanPolicy.id == run.policy_id).first()
        if not policy:
            raise ValueError(f"Policy {run.policy_id} not found")

        policy_params = _load_policy_params(policy)
        business_days = _get_business_days(run.date_from, run.date_to)

        if not business_days:
            raise ValueError("No business days in date range")

        total_predictions = 0
        correct_count = 0
        abstain_count = 0

        from app.advan.event_retriever import retrieve_similar_events
        from app.advan.llm_forecaster import (
            predict_stock,
            predict_stock_heuristic,
            predict_stock_heuristic_v2,
        )

        use_v2 = policy_params.get("template_config", {}).get("use_v2_heuristic", False)

        for day in business_days:
            events_by_ticker = _get_events_for_date(db, run.market, day)

            if not events_by_ticker:
                continue

            for ticker, events in events_by_ticker.items():
                # 템플릿 설정에 따라 이벤트 수 제한
                max_events = policy_params.get("template_config", {}).get("max_events_per_stock", 5)
                events = events[:max_events]

                # 피처 조회
                feature = (
                    db.query(AdvanFeatureDaily)
                    .filter(
                        AdvanFeatureDaily.ticker == ticker,
                        AdvanFeatureDaily.trade_date == day,
                    )
                    .first()
                )

                # 유사 이벤트 검색
                similar = None
                if events and policy_params.get("template_config", {}).get("include_similar_events", True):
                    try:
                        similar = retrieve_similar_events(
                            db, events[0], policy_params.get("retrieval_config", {}), day
                        )
                    except Exception as e:
                        logger.debug("Similar event retrieval failed: %s", e)

                # 예측 실행
                try:
                    result = predict_stock(
                        db, ticker, events, feature, similar,
                        policy_params, run.horizon,
                    )
                except Exception:
                    if use_v2:
                        result = predict_stock_heuristic_v2(events, feature, policy_params, prediction_date=day)
                    else:
                        result = predict_stock_heuristic(events, feature, policy_params)

                # 예측 저장
                pred = AdvanPrediction(
                    run_id=run_id,
                    event_id=events[0].id if events else None,
                    policy_id=run.policy_id,
                    ticker=ticker,
                    prediction_date=day,
                    horizon=run.horizon,
                    prediction=result.get("prediction", "Abstain"),
                    p_up=result.get("p_up", 0.33),
                    p_down=result.get("p_down", 0.33),
                    p_flat=result.get("p_flat", 0.34),
                    trade_action=result.get("trade_action", "skip"),
                    position_size=result.get("position_size", 0.0),
                    top_drivers=json.dumps(result.get("top_drivers", []), ensure_ascii=False),
                    invalidators=json.dumps(result.get("invalidators", []), ensure_ascii=False),
                    reasoning=result.get("reasoning"),
                )
                db.add(pred)
                db.flush()  # ID 할당

                # 라벨 생성
                label = _generate_label(db, pred, run.label_threshold_pct)
                if label:
                    db.add(label)
                    if label.is_correct is True:
                        correct_count += 1

                total_predictions += 1
                if result.get("prediction") == "Abstain":
                    abstain_count += 1

            # 일 단위 커밋
            db.commit()

        # 집계 업데이트
        evaluated = total_predictions - abstain_count
        run.total_predictions = total_predictions
        run.correct_count = correct_count
        run.abstain_count = abstain_count
        run.accuracy_rate = round(correct_count / evaluated, 4) if evaluated > 0 else 0.0
        run.duration_seconds = round(time.time() - start_time, 2)
        run.status = "completed"
        run.completed_at = datetime.now(UTC)

        # 고급 메트릭 계산
        try:
            from app.advan.evaluator import evaluate_run
            metrics = evaluate_run(db, run_id)
            run.brier_score = metrics.get("brier")
            run.calibration_error = metrics.get("calibration_error")
            run.auc_score = metrics.get("auc")
            run.f1_score = metrics.get("f1")
            run.avg_excess_return = metrics.get("avg_excess_return")
            run.by_event_type_metrics = json.dumps(
                metrics.get("by_event_type", {}), ensure_ascii=False
            )
        except Exception as e:
            logger.warning("Advanced metrics calculation failed: %s", e)

        db.commit()
        logger.info(
            "Simulation run %d completed: %d predictions, %.1f%% accuracy",
            run_id, total_predictions, run.accuracy_rate * 100,
        )

    except Exception as e:
        logger.error("Simulation run %d failed: %s", run_id, e)
        run.status = "failed"
        run.error_message = str(e)[:500]
        run.duration_seconds = round(time.time() - start_time, 2)
        db.commit()
