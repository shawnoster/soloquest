"""Tests for momentum tracking and burn logic."""

from wyrd.engine.momentum import (
    MOMENTUM_MAX,
    MOMENTUM_MIN,
    MOMENTUM_RESET_DEFAULT,
    adjust_momentum,
    clamp_momentum,
    momentum_after_burn,
)


class TestClampMomentum:
    def test_clamps_below_min(self):
        assert clamp_momentum(-10) == MOMENTUM_MIN

    def test_clamps_above_max(self):
        assert clamp_momentum(15) == MOMENTUM_MAX

    def test_passes_through_min(self):
        assert clamp_momentum(MOMENTUM_MIN) == MOMENTUM_MIN

    def test_passes_through_max(self):
        assert clamp_momentum(MOMENTUM_MAX) == MOMENTUM_MAX

    def test_passes_through_midrange(self):
        assert clamp_momentum(0) == 0
        assert clamp_momentum(5) == 5
        assert clamp_momentum(-3) == -3


class TestMomentumAfterBurn:
    def test_resets_to_default(self):
        assert momentum_after_burn(10) == MOMENTUM_RESET_DEFAULT

    def test_reset_regardless_of_current(self):
        for current in [-6, -1, 0, 2, 5, 10]:
            assert momentum_after_burn(current) == MOMENTUM_RESET_DEFAULT


class TestAdjustMomentum:
    def test_adds_positive_delta(self):
        assert adjust_momentum(3, 2) == 5

    def test_adds_negative_delta(self):
        assert adjust_momentum(3, -2) == 1

    def test_clamps_at_max(self):
        assert adjust_momentum(8, 5) == MOMENTUM_MAX

    def test_clamps_at_min(self):
        assert adjust_momentum(-4, -5) == MOMENTUM_MIN

    def test_zero_delta_unchanged(self):
        assert adjust_momentum(4, 0) == 4

    def test_custom_max_momentum(self):
        assert adjust_momentum(3, 4, max_momentum=5) == 5

    def test_custom_max_respected_over_default(self):
        # With a lower max, should clamp to custom max, not MOMENTUM_MAX
        assert adjust_momentum(8, 1, max_momentum=8) == 8
        assert adjust_momentum(7, 3, max_momentum=8) == 8

    def test_result_never_below_min(self):
        assert adjust_momentum(MOMENTUM_MIN, -1) == MOMENTUM_MIN
