"""Tests for feature_config module."""

import pytest
from app.processing.feature_config import (
    TIER_1_FEATURES,
    TIER_2_FEATURES,
    TIER_3_FEATURES,
    REMOVED_FEATURES,
    get_features_for_tier,
    get_min_samples_for_tier,
    get_feature_count_for_tier,
)


class TestTierDefinitions:
    def test_tier1_has_8_features(self):
        assert len(TIER_1_FEATURES) == 8

    def test_tier2_has_16_features(self):
        assert len(TIER_2_FEATURES) == 16

    def test_tier3_has_20_features(self):
        assert len(TIER_3_FEATURES) == 20

    def test_tier2_contains_all_tier1(self):
        for f in TIER_1_FEATURES:
            assert f in TIER_2_FEATURES

    def test_tier3_contains_all_tier2(self):
        for f in TIER_2_FEATURES:
            assert f in TIER_3_FEATURES

    def test_no_removed_features_in_tiers(self):
        all_tier_features = set(TIER_3_FEATURES)
        for removed in REMOVED_FEATURES:
            assert removed not in all_tier_features, f"Removed feature '{removed}' found in tiers"


class TestGetFeaturesForTier:
    def test_tier1(self):
        features = get_features_for_tier(1)
        assert features == list(TIER_1_FEATURES)

    def test_tier2(self):
        features = get_features_for_tier(2)
        assert len(features) == 16

    def test_tier3(self):
        features = get_features_for_tier(3)
        assert len(features) == 20

    def test_returns_copy(self):
        f1 = get_features_for_tier(1)
        f1.append("extra")
        assert len(get_features_for_tier(1)) == 8

    def test_invalid_tier_raises(self):
        with pytest.raises(ValueError, match="Invalid tier"):
            get_features_for_tier(0)
        with pytest.raises(ValueError, match="Invalid tier"):
            get_features_for_tier(4)


class TestGetMinSamples:
    def test_tier1_needs_200(self):
        assert get_min_samples_for_tier(1) == 200

    def test_tier2_needs_500(self):
        assert get_min_samples_for_tier(2) == 500

    def test_tier3_needs_1000(self):
        assert get_min_samples_for_tier(3) == 1000

    def test_invalid_tier_raises(self):
        with pytest.raises(ValueError):
            get_min_samples_for_tier(0)


class TestFeatureCount:
    def test_tier1_count(self):
        assert get_feature_count_for_tier(1) == 8

    def test_tier2_count(self):
        assert get_feature_count_for_tier(2) == 16

    def test_tier3_count(self):
        assert get_feature_count_for_tier(3) == 20
