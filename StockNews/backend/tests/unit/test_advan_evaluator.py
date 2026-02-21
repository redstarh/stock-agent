"""Advan Evaluator 단위 테스트."""

import pytest

from app.advan.evaluator import (
    _accuracy_f1,
    _auc_binary,
    _brier_score,
    _by_direction_metrics,
    _by_event_type_metrics,
    _calibration_error,
    _robustness_metrics,
)


class TestBrierScore:
    """Brier Score 계산 테스트."""

    def test_perfect_prediction(self):
        """완벽한 예측: Brier = 0."""
        predictions = [
            {"p_up": 1.0, "p_down": 0.0, "p_flat": 0.0, "actual_label": "Up"},
            {"p_up": 0.0, "p_down": 1.0, "p_flat": 0.0, "actual_label": "Down"},
            {"p_up": 0.0, "p_down": 0.0, "p_flat": 1.0, "actual_label": "Flat"},
        ]
        assert _brier_score(predictions) == pytest.approx(0.0)

    def test_worst_prediction(self):
        """최악의 예측: Brier = 2.0."""
        predictions = [
            {"p_up": 0.0, "p_down": 1.0, "p_flat": 0.0, "actual_label": "Up"},
        ]
        # (0-1)^2 + (1-0)^2 + (0-0)^2 = 2.0
        assert _brier_score(predictions) == pytest.approx(2.0)

    def test_random_prediction(self):
        """랜덤 예측 (1/3씩): Brier ≈ 0.667."""
        predictions = [
            {"p_up": 0.33, "p_down": 0.33, "p_flat": 0.34, "actual_label": "Up"},
        ]
        expected = (0.33 - 1) ** 2 + (0.33 - 0) ** 2 + (0.34 - 0) ** 2
        assert _brier_score(predictions) == pytest.approx(expected, abs=0.01)

    def test_empty_predictions(self):
        """빈 예측: Brier = 1.0."""
        assert _brier_score([]) == 1.0

    def test_skip_none_labels(self):
        """라벨 없는 예측은 건너뜀."""
        predictions = [
            {"p_up": 1.0, "p_down": 0.0, "p_flat": 0.0, "actual_label": "Up"},
            {"p_up": 0.5, "p_down": 0.5, "p_flat": 0.0, "actual_label": None},
        ]
        assert _brier_score(predictions) == pytest.approx(0.0)


class TestCalibrationError:
    """Calibration Error 계산 테스트."""

    def test_perfect_calibration(self):
        """완벽한 보정: ECE ≈ 0."""
        # 모든 예측이 정확하고 confidence가 1.0에 가까움
        predictions = [
            {"prediction": "Up", "p_up": 0.9, "p_down": 0.05, "p_flat": 0.05, "actual_label": "Up"},
            {"prediction": "Down", "p_up": 0.05, "p_down": 0.9, "p_flat": 0.05, "actual_label": "Down"},
        ]
        ece = _calibration_error(predictions)
        assert ece < 0.2  # 샘플 수가 적어 완벽하지는 않음

    def test_empty_predictions(self):
        assert _calibration_error([]) == 1.0

    def test_abstain_excluded(self):
        """Abstain 예측은 제외."""
        predictions = [
            {"prediction": "Abstain", "p_up": 0.33, "p_down": 0.33, "p_flat": 0.34, "actual_label": "Up"},
        ]
        assert _calibration_error(predictions) == 1.0  # Abstain만 있으므로 빈 결과


class TestAccuracyF1:
    """Accuracy/F1 계산 테스트."""

    def test_perfect_accuracy(self):
        predictions = [
            {"prediction": "Up", "actual_label": "Up"},
            {"prediction": "Down", "actual_label": "Down"},
            {"prediction": "Flat", "actual_label": "Flat"},
        ]
        result = _accuracy_f1(predictions)
        assert result["accuracy"] == 1.0
        assert result["f1"] == 1.0

    def test_zero_accuracy(self):
        predictions = [
            {"prediction": "Up", "actual_label": "Down"},
            {"prediction": "Down", "actual_label": "Flat"},
            {"prediction": "Flat", "actual_label": "Up"},
        ]
        result = _accuracy_f1(predictions)
        assert result["accuracy"] == 0.0

    def test_abstain_excluded(self):
        predictions = [
            {"prediction": "Up", "actual_label": "Up"},
            {"prediction": "Abstain", "actual_label": "Down"},
        ]
        result = _accuracy_f1(predictions)
        assert result["accuracy"] == 1.0  # Abstain 제외, 1/1

    def test_empty(self):
        result = _accuracy_f1([])
        assert result["accuracy"] == 0.0
        assert result["f1"] == 0.0


class TestAUCBinary:
    """AUC 계산 테스트."""

    def test_perfect_separation(self):
        """완벽 분리: AUC = 1.0."""
        predictions = [
            {"prediction": "Up", "p_up": 0.9, "actual_label": "Up"},
            {"prediction": "Up", "p_up": 0.8, "actual_label": "Up"},
            {"prediction": "Down", "p_up": 0.2, "actual_label": "Down"},
            {"prediction": "Down", "p_up": 0.1, "actual_label": "Down"},
        ]
        auc = _auc_binary(predictions)
        assert auc == 1.0

    def test_random_prediction(self):
        """랜덤: AUC ≈ 0.5."""
        predictions = [
            {"prediction": "Up", "p_up": 0.5, "actual_label": "Up"},
            {"prediction": "Down", "p_up": 0.5, "actual_label": "Down"},
        ]
        auc = _auc_binary(predictions)
        assert auc == 0.5

    def test_no_positives(self):
        predictions = [
            {"prediction": "Down", "p_up": 0.2, "actual_label": "Down"},
        ]
        assert _auc_binary(predictions) is None


class TestByEventType:
    """이벤트 타입별 분해 테스트."""

    def test_multiple_types(self):
        predictions = [
            {"prediction": "Up", "actual_label": "Up", "event_type": "실적"},
            {"prediction": "Down", "actual_label": "Down", "event_type": "실적"},
            {"prediction": "Up", "actual_label": "Down", "event_type": "수주"},
        ]
        result = _by_event_type_metrics(predictions)
        assert "실적" in result
        assert "수주" in result
        assert result["실적"]["accuracy"] == 1.0
        assert result["수주"]["accuracy"] == 0.0
        assert result["실적"]["total"] == 2
        assert result["수주"]["total"] == 1


class TestByDirection:
    """방향별 분해 테스트."""

    def test_direction_stats(self):
        predictions = [
            {"prediction": "Up", "actual_label": "Up"},
            {"prediction": "Up", "actual_label": "Down"},
            {"prediction": "Down", "actual_label": "Down"},
        ]
        result = _by_direction_metrics(predictions)
        assert result["Up"]["total"] == 2
        assert result["Up"]["correct"] == 1
        assert result["Up"]["accuracy"] == 0.5
        assert result["Down"]["accuracy"] == 1.0


class TestRobustness:
    """구간별 안정성 테스트."""

    def test_insufficient_data(self):
        predictions = [{"prediction": "Up", "actual_label": "Up", "prediction_date": "2024-01-01"}]
        result = _robustness_metrics(predictions)
        assert result["variance"] is None

    def test_stable_predictions(self):
        """안정적인 예측: 낮은 분산."""
        predictions = []
        for i in range(20):
            predictions.append({
                "prediction": "Up",
                "actual_label": "Up",
                "prediction_date": f"2024-01-{i+1:02d}",
            })
        result = _robustness_metrics(predictions)
        assert result["variance"] is not None
        assert result["variance"] == 0.0  # 모두 정확 → 분산 0
