"""Tests for move resolution logic."""

from wyrd.engine.moves import (
    OutcomeTier,
    check_match,
    momentum_burn_outcome,
    resolve_move,
    resolve_outcome,
    would_momentum_improve,
)


class TestResolveOutcome:
    def test_strong_hit_beats_both(self):
        assert resolve_outcome(9, 4, 7) == OutcomeTier.STRONG_HIT

    def test_weak_hit_beats_one(self):
        assert resolve_outcome(5, 3, 8) == OutcomeTier.WEAK_HIT

    def test_miss_beats_neither(self):
        assert resolve_outcome(2, 5, 8) == OutcomeTier.MISS

    def test_exact_tie_does_not_beat(self):
        # Action score must be strictly greater than challenge die
        assert resolve_outcome(5, 5, 3) == OutcomeTier.WEAK_HIT
        assert resolve_outcome(5, 5, 5) == OutcomeTier.MISS

    def test_action_score_10_cap(self):
        # resolve_move caps at 10
        result = resolve_move(action_die=6, stat=5, adds=3, c1=9, c2=8)
        assert result.action_score == 10

    def test_strong_hit_at_cap(self):
        result = resolve_move(action_die=6, stat=5, adds=0, c1=9, c2=8)
        assert result.action_score == 10
        assert result.outcome == OutcomeTier.STRONG_HIT


class TestCheckMatch:
    def test_match_detected(self):
        assert check_match(7, 7) is True

    def test_no_match(self):
        assert check_match(3, 8) is False

    def test_match_on_ones(self):
        assert check_match(1, 1) is True


class TestMomentumBurn:
    def test_burn_improves_miss_to_strong(self):
        # momentum 8 vs challenge 3 and 5 = strong hit
        outcome = momentum_burn_outcome(8, 3, 5)
        assert outcome == OutcomeTier.STRONG_HIT

    def test_would_momentum_improve_true(self):
        # current outcome is miss, momentum would give strong hit
        assert would_momentum_improve(OutcomeTier.MISS, 8, 3, 5) is True

    def test_would_momentum_improve_false_already_strong(self):
        assert would_momentum_improve(OutcomeTier.STRONG_HIT, 8, 3, 5) is False

    def test_would_momentum_improve_false_zero_momentum(self):
        assert would_momentum_improve(OutcomeTier.MISS, 0, 5, 8) is False

    def test_would_momentum_improve_false_negative(self):
        assert would_momentum_improve(OutcomeTier.MISS, -2, 5, 8) is False


class TestResolveMove:
    def test_basic_strong_hit(self):
        result = resolve_move(action_die=5, stat=3, adds=0, c1=4, c2=6)
        assert result.action_score == 8
        assert result.outcome == OutcomeTier.STRONG_HIT
        assert result.match is False
        assert result.burned_momentum is False

    def test_basic_miss(self):
        result = resolve_move(action_die=1, stat=1, adds=0, c1=8, c2=9)
        assert result.outcome == OutcomeTier.MISS

    def test_burn_momentum_sets_flag(self):
        result = resolve_move(action_die=1, stat=1, adds=0, c1=8, c2=9, momentum=8, burn=True)
        assert result.burned_momentum is True
        assert result.momentum_used == 8

    def test_match_detected_in_result(self):
        result = resolve_move(action_die=1, stat=1, adds=0, c1=6, c2=6)
        assert result.match is True

    def test_adds_are_included(self):
        result = resolve_move(action_die=3, stat=2, adds=2, c1=1, c2=1)
        assert result.action_score == 7

    def test_beat_flags(self):
        result = resolve_move(action_die=5, stat=3, adds=0, c1=4, c2=9)
        assert result.beats_c1 is True
        assert result.beats_c2 is False
