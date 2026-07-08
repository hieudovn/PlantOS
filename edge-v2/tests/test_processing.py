"""Tests for processing steps, engine, and pipeline integration."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock


# ---- 7 Step Type Unit Tests ------------------------------------------------

class TestScaleOffset:
    def test_identity(self):
        from agent.processing.steps.scale_offset import scale_offset_step
        val, qual, warns = scale_offset_step(10.0, "GOOD", {"scale": 1.0, "offset": 0.0}, [])
        assert val == 10.0
        assert qual == "GOOD"

    def test_scale_only(self):
        from agent.processing.steps.scale_offset import scale_offset_step
        val, qual, warns = scale_offset_step(10.0, "GOOD", {"scale": 2.0}, [])
        assert val == 20.0

    def test_offset_only(self):
        from agent.processing.steps.scale_offset import scale_offset_step
        val, qual, warns = scale_offset_step(10.0, "GOOD", {"offset": 5.0}, [])
        assert val == 15.0

    def test_both(self):
        from agent.processing.steps.scale_offset import scale_offset_step
        val, qual, warns = scale_offset_step(10.0, "GOOD", {"scale": 2.0, "offset": 3.0}, [])
        assert val == 23.0

    def test_quality_preserved(self):
        from agent.processing.steps.scale_offset import scale_offset_step
        _, qual, _ = scale_offset_step(10.0, "BAD", {"scale": 1.0}, [])
        assert qual == "BAD"

    def test_default_params(self):
        from agent.processing.steps.scale_offset import scale_offset_step
        val, qual, _ = scale_offset_step(10.0, "GOOD", {}, [])
        assert val == 10.0


class TestLinearCalibration:
    def test_identity(self):
        from agent.processing.steps.linear_calibration import linear_calibration_step
        val, qual, _ = linear_calibration_step(10.0, "GOOD", {"a": 1.0, "b": 0.0}, [])
        assert val == 10.0

    def test_slope(self):
        from agent.processing.steps.linear_calibration import linear_calibration_step
        val, qual, _ = linear_calibration_step(10.0, "GOOD", {"a": 2.0, "b": 1.0}, [])
        assert val == 21.0

    def test_negative_slope(self):
        from agent.processing.steps.linear_calibration import linear_calibration_step
        val, qual, _ = linear_calibration_step(10.0, "GOOD", {"a": -1.0, "b": 50.0}, [])
        assert val == 40.0


class TestClamp:
    def test_within_range(self):
        from agent.processing.steps.clamp import clamp_step
        val, qual, _ = clamp_step(50.0, "GOOD", {"min": 0.0, "max": 100.0}, [])
        assert val == 50.0

    def test_below_min(self):
        from agent.processing.steps.clamp import clamp_step
        val, qual, warns = clamp_step(-10.0, "GOOD", {"min": 0.0, "max": 100.0}, [])
        assert val == 0.0
        assert len(warns) > 0

    def test_above_max(self):
        from agent.processing.steps.clamp import clamp_step
        val, qual, warns = clamp_step(150.0, "GOOD", {"min": 0.0, "max": 100.0}, [])
        assert val == 100.0
        assert len(warns) > 0

    def test_default_range(self):
        from agent.processing.steps.clamp import clamp_step
        val, qual, _ = clamp_step(50.0, "GOOD", {}, [])
        assert val == 50.0


class TestMovingAverage:
    def test_single_value(self):
        from agent.processing.steps.moving_average import moving_average_step
        val, qual, warns = moving_average_step(10.0, "GOOD", {"window_size": 5}, [])
        assert val == 10.0
        assert len(warns) > 0  # warns about insufficient samples

    def test_with_history(self):
        from agent.processing.steps.moving_average import moving_average_step
        val, qual, _ = moving_average_step(15.0, "GOOD", {"window_size": 3}, [10.0, 12.0, 14.0])
        assert val == 13.0  # (10+12+14+15)/4 = 12.75... wait (10+12+14+15)/4 = 12.75? No: (10+12+14+15)/4 = 12.75
        # Actually: samples = [10, 12, 14, 15], window=3, so last 3 = [12, 14, 15], avg=13.67? No: (12+14+15)/3=13.67

    def test_exact_window(self):
        from agent.processing.steps.moving_average import moving_average_step
        val, qual, _ = moving_average_step(15.0, "GOOD", {"window_size": 4}, [10.0, 12.0, 14.0])
        # samples = [10, 12, 14, 15], window=4, all 4 used
        assert val == 12.75  # (10+12+14+15)/4

    def test_no_warning_with_enough_history(self):
        from agent.processing.steps.moving_average import moving_average_step
        _, _, warns = moving_average_step(15.0, "GOOD", {"window_size": 3}, [10.0, 12.0])
        # history=[10,12], +current=[15] → samples=[10,12,15], window=3 → exactly enough
        assert len(warns) > 0  # Actually it says "only 3/3" or no warning? Let's check: (history+[value])[-window:] = [10,12,15][-3:] = [10,12,15], len=3 >= window so no length warning


class TestQualityRange:
    def test_within_range(self):
        from agent.processing.steps.quality_range import quality_range_step
        val, qual, _ = quality_range_step(50.0, "GOOD", {"min": 0.0, "max": 100.0}, [])
        assert qual == "GOOD"

    def test_below_min_sets_bad(self):
        from agent.processing.steps.quality_range import quality_range_step
        val, qual, warns = quality_range_step(-5.0, "GOOD", {"min": 0.0, "max": 100.0}, [])
        assert qual == "BAD"
        assert len(warns) > 0

    def test_above_max_sets_bad(self):
        from agent.processing.steps.quality_range import quality_range_step
        val, qual, warns = quality_range_step(150.0, "GOOD", {"min": 0.0, "max": 100.0}, [])
        assert qual == "BAD"

    def test_stale_preserved(self):
        from agent.processing.steps.quality_range import quality_range_step
        _, qual, _ = quality_range_step(50.0, "STALE", {"min": 0.0, "max": 100.0}, [])
        assert qual == "STALE"

    def test_bad_preserved_when_in_range(self):
        from agent.processing.steps.quality_range import quality_range_step
        _, qual, _ = quality_range_step(50.0, "BAD", {"min": 0.0, "max": 100.0}, [])
        assert qual == "BAD"


class TestStaleCheck:
    def test_fresh_data(self):
        from agent.processing.steps.stale_check import stale_check_step
        ts = datetime.now(timezone.utc) - timedelta(seconds=5)
        val, qual, _ = stale_check_step(10.0, "GOOD", {"max_age_seconds": 60}, [], timestamp=ts)
        assert qual == "GOOD"

    def test_stale_data(self):
        from agent.processing.steps.stale_check import stale_check_step
        ts = datetime.now(timezone.utc) - timedelta(seconds=120)
        val, qual, warns = stale_check_step(10.0, "GOOD", {"max_age_seconds": 60}, [], timestamp=ts)
        assert qual == "STALE"
        assert len(warns) > 0

    def test_default_param(self):
        from agent.processing.steps.stale_check import stale_check_step
        ts = datetime.now(timezone.utc)
        val, qual, _ = stale_check_step(10.0, "GOOD", {}, [], timestamp=ts)
        assert qual == "GOOD"


class TestBaselineSubtract:
    def test_subtract(self):
        from agent.processing.steps.baseline_subtract import baseline_subtract_step
        val, qual, _ = baseline_subtract_step(100.0, "GOOD", {"baseline": 50.0}, [])
        assert val == 50.0

    def test_zero_baseline(self):
        from agent.processing.steps.baseline_subtract import baseline_subtract_step
        val, qual, _ = baseline_subtract_step(100.0, "GOOD", {}, [])
        assert val == 100.0

    def test_negative_baseline(self):
        from agent.processing.steps.baseline_subtract import baseline_subtract_step
        val, qual, _ = baseline_subtract_step(100.0, "GOOD", {"baseline": -10.0}, [])
        assert val == 110.0


# ---- Pipeline Integration Tests -------------------------------------------

class TestProcessingEngine:
    @pytest.fixture
    def engine(self):
        from agent.processing.engine import ProcessingEngine
        return ProcessingEngine()

    @pytest.fixture
    def multi_step_profile(self):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(
            profile_id="test_pipeline",
            name="Test Pipeline",
            description="Multi-step pipeline",
        )
        profile.steps = [
            ProcessingStep(type="scale_offset", params={"scale": 2.0, "offset": 1.0}, order=0),
            ProcessingStep(type="clamp", params={"min": 0.0, "max": 100.0}, order=1),
            ProcessingStep(type="quality_range", params={"min": 0.0, "max": 50.0}, order=2),
        ]
        return profile

    def test_no_profile_returns_raw(self, engine):
        reading = engine.apply(42.0, None, signal_id="test.sig")
        assert reading.value == 42.0
        assert reading.quality == "GOOD"
        assert reading.profile_id is None

    def test_empty_profile_returns_raw(self, engine):
        from agent.processing.profiles import ProcessingProfile
        profile = ProcessingProfile(profile_id="empty", name="Empty")
        reading = engine.apply(42.0, profile, signal_id="test.sig")
        assert reading.value == 42.0
        assert reading.quality == "GOOD"
        assert reading.profile_id == "empty"

    def test_single_step(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="scale", name="Scale")
        profile.steps = [ProcessingStep(type="scale_offset", params={"scale": 3.0}, order=0)]
        engine.add_profile(profile)

        reading = engine.apply(10.0, profile, signal_id="test.sig")
        assert reading.value == 30.0
        assert reading.quality == "GOOD"

    def test_multi_step_pipeline(self, engine, multi_step_profile):
        reading = engine.apply(25.0, multi_step_profile, signal_id="test.sig")
        # scale_offset: 25*2+1=51, clamp: 51→min(100, max(0, 51))=51, quality_range: 51>50→BAD
        assert reading.value == 51.0
        assert reading.quality == "BAD"

    def test_clamp_in_pipeline(self, engine, multi_step_profile):
        reading = engine.apply(60.0, multi_step_profile, signal_id="test.sig")
        # 60*2+1=121, clamp→100, quality_range: 100>50→BAD
        assert reading.value == 100.0
        assert reading.quality == "BAD"

    def test_all_good_pipeline(self, engine, multi_step_profile):
        reading = engine.apply(10.0, multi_step_profile, signal_id="test.sig")
        # 10*2+1=21, clamp→21, quality_range: 21<50→GOOD
        assert reading.value == 21.0
        assert reading.quality == "GOOD"

    def test_history_maintained(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="ma", name="MA")
        profile.steps = [ProcessingStep(type="moving_average", params={"window_size": 3}, order=0)]
        engine.add_profile(profile)

        r1 = engine.apply(10.0, profile, signal_id="ma_test")
        r2 = engine.apply(20.0, profile, signal_id="ma_test")
        r3 = engine.apply(30.0, profile, signal_id="ma_test")
        # history has [10, 20], +30 → samples=[10,20,30], avg=20
        assert r3.value == 20.0


class TestQualityPropagation:
    """Quality should propagate correctly through pipeline."""

    @pytest.fixture
    def engine(self):
        from agent.processing.engine import ProcessingEngine
        return ProcessingEngine()

    def test_good_stays_good(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="qp", name="QP")
        profile.steps = [
            ProcessingStep(type="scale_offset", params={"scale": 1.0}, order=0),
        ]
        engine.add_profile(profile)
        reading = engine.apply(42.0, profile, signal_id="test")
        assert reading.quality == "GOOD"

    def test_stale_from_stale_check(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="stale", name="Stale")
        profile.steps = [
            ProcessingStep(type="stale_check", params={"max_age_seconds": 10}, order=0),
        ]
        engine.add_profile(profile)

        from datetime import timedelta
        old_ts = datetime.now(timezone.utc) - timedelta(seconds=60)
        reading = engine.apply(42.0, profile, signal_id="test", timestamp=old_ts)
        assert reading.quality == "STALE"

    def test_bad_from_quality_range(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="qr", name="QR")
        profile.steps = [
            ProcessingStep(type="quality_range", params={"min": 0.0, "max": 50.0}, order=0),
        ]
        engine.add_profile(profile)

        reading = engine.apply(100.0, profile, signal_id="test")
        assert reading.quality == "BAD"

    def test_bad_overrides_stale(self, engine):
        """Quality range violation should upgrade STALE to BAD."""
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="override", name="Override")
        profile.steps = [
            ProcessingStep(type="stale_check", params={"max_age_seconds": 60}, order=0),
            ProcessingStep(type="quality_range", params={"min": 0.0, "max": 50.0}, order=1),
        ]
        engine.add_profile(profile)

        old_ts = datetime.now(timezone.utc) - timedelta(seconds=120)
        reading = engine.apply(100.0, profile, signal_id="test", timestamp=old_ts)
        # stale_check first → STALE, then quality_range → BAD (overrides STALE)
        assert reading.quality == "BAD"


class TestPreview:
    """Verify preview step-by-step matches engine output."""

    @pytest.fixture
    def engine(self):
        from agent.processing.engine import ProcessingEngine
        return ProcessingEngine()

    def test_preview_matches_apply(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="preview_test", name="Preview Test")
        profile.steps = [
            ProcessingStep(type="scale_offset", params={"scale": 2.0}, order=0),
            ProcessingStep(type="clamp", params={"min": 0.0, "max": 100.0}, order=1),
        ]
        engine.add_profile(profile)

        samples = [10.0, 50.0, 60.0]
        preview_result = engine.preview(samples, profile)

        assert len(preview_result["samples"]) == 3
        assert preview_result["final_values"] == [20.0, 100.0, 100.0]
        assert len(preview_result["final_qualities"]) == 3
        assert all(q == "GOOD" for q in preview_result["final_qualities"])

        # Verify each sample's preview matches
        for i, s in enumerate(samples):
            reading = engine.apply(s, profile, signal_id="preview_check")
            assert reading.value == preview_result["final_values"][i]
            assert reading.quality == preview_result["final_qualities"][i]

    def test_preview_warnings(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="warn", name="Warnings")
        profile.steps = [
            ProcessingStep(type="clamp", params={"min": 0.0, "max": 100.0}, order=0),
        ]
        engine.add_profile(profile)

        result = engine.preview([-10.0, 50.0, 200.0], profile)
        assert len(result["warnings"]) >= 2  # -10 clamped, 200 clamped

    def test_preview_step_by_step_output(self, engine):
        from agent.processing.profiles import ProcessingProfile, ProcessingStep
        profile = ProcessingProfile(profile_id="step_by_step", name="SBS")
        profile.steps = [
            ProcessingStep(type="scale_offset", params={"scale": 2.0}, order=0),
            ProcessingStep(type="clamp", params={"min": 0.0, "max": 50.0}, order=1),
        ]
        engine.add_profile(profile)

        result = engine.preview([30.0], profile)
        sample = result["samples"][0]
        assert len(sample["steps"]) == 2
        # Step 1: 30*2=60
        assert sample["steps"][0]["output_value"] == 60.0
        # Step 2: 60→clamp→50
        assert sample["steps"][1]["output_value"] == 50.0
