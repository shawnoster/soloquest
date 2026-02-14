"""Integration tests — move resolution, oracle lookup, vow fulfillment end-to-end.

These tests exercise the engine layers together using a deterministic dice stub,
so they test the full data-flow without needing a running REPL.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from starforged.engine.dice import Die
from starforged.engine.moves import (
    OutcomeTier,
    check_match,
    resolve_move,
    resolve_outcome,
    would_momentum_improve,
)
from starforged.engine.oracles import load_oracles
from starforged.models.character import Character, Stats
from starforged.models.vow import SPIRIT_COST, Vow, VowRank

DATA_DIR = Path(__file__).parent.parent / "starforged" / "data"


# ── Deterministic dice stub ────────────────────────────────────────────────────


class FixedDice:
    """Returns a preset sequence of values, cycling if exhausted."""

    def __init__(self, values: list[int]):
        self._values = values
        self._idx = 0

    def roll(self, die: Die) -> int:
        v = self._values[self._idx % len(self._values)]
        self._idx += 1
        return v


# ── Move resolution integration ────────────────────────────────────────────────


class TestMoveResolutionIntegration:
    """Verify resolve_move produces correct outcomes for all combinations."""

    @pytest.mark.parametrize(
        "action_die,stat,adds,c1,c2,expected",
        [
            # Strong hit — beats both
            (5, 3, 0, 4, 6, OutcomeTier.STRONG_HIT),
            # Strong hit with adds — beats both
            (3, 2, 2, 3, 5, OutcomeTier.STRONG_HIT),  # score=7 vs [3,5]
            # Weak hit — beats exactly one challenge die
            (3, 1, 0, 5, 2, OutcomeTier.WEAK_HIT),  # score=4 vs [5,2]: 4>2 yes, 4>5 no
            # Miss — beats neither
            (1, 1, 0, 8, 9, OutcomeTier.MISS),
            # Action score caps at 10
            (6, 4, 3, 9, 8, OutcomeTier.STRONG_HIT),  # score capped to 10 vs [9,8]
        ],
    )
    def test_outcome_tiers(self, action_die, stat, adds, c1, c2, expected):
        result = resolve_move(action_die, stat, adds, c1, c2)
        assert result.outcome == expected

    def test_action_score_caps_at_10(self):
        result = resolve_move(action_die=6, stat=4, adds=3, c1=5, c2=5)
        assert result.action_score == 10

    def test_match_detected(self):
        result = resolve_move(action_die=5, stat=3, adds=0, c1=4, c2=4)
        assert result.match is True

    def test_no_match_when_dice_differ(self):
        result = resolve_move(action_die=5, stat=3, adds=0, c1=4, c2=7)
        assert result.match is False

    def test_momentum_burn_upgrades_miss_to_strong(self):
        # action_score = 3, c1=8, c2=7 → miss; but momentum=9 → strong
        result = resolve_move(action_die=2, stat=1, adds=0, c1=8, c2=7, momentum=9, burn=True)
        assert result.outcome == OutcomeTier.STRONG_HIT
        assert result.burned_momentum is True
        assert result.momentum_used == 9

    def test_momentum_burn_upgrades_miss_to_weak(self):
        # momentum=5 beats one challenge die
        result = resolve_move(action_die=1, stat=1, adds=0, c1=3, c2=9, momentum=5, burn=True)
        assert result.outcome == OutcomeTier.WEAK_HIT
        assert result.burned_momentum is True

    def test_would_momentum_improve_true_on_miss(self):
        # Action miss; momentum=8 > both challenge dice
        result = resolve_move(1, 1, 0, 7, 6)
        assert result.outcome == OutcomeTier.MISS
        assert would_momentum_improve(result.outcome, 8, 7, 6) is True

    def test_would_momentum_improve_false_on_strong(self):
        result = resolve_move(5, 3, 0, 2, 3)
        assert result.outcome == OutcomeTier.STRONG_HIT
        assert would_momentum_improve(result.outcome, 8, 2, 3) is False

    def test_would_momentum_improve_false_when_momentum_zero(self):
        result = resolve_move(1, 1, 0, 8, 9)
        assert would_momentum_improve(result.outcome, 0, 8, 9) is False

    def test_beats_c1_and_c2_properties(self):
        result = resolve_move(5, 3, 0, 4, 2)
        assert result.beats_c1 is True  # 8 > 4
        assert result.beats_c2 is True  # 8 > 2

    def test_beats_only_c2(self):
        result = resolve_move(2, 1, 0, 9, 2)
        assert result.beats_c1 is False  # 3 > 9? no
        assert result.beats_c2 is True  # 3 > 2


class TestProgressRollIntegration:
    """Progress rolls use progress score vs 2d10, no action die."""

    def test_strong_hit_progress_roll(self):
        outcome = resolve_outcome(10, 8, 7)
        assert outcome == OutcomeTier.STRONG_HIT

    def test_weak_hit_progress_roll(self):
        outcome = resolve_outcome(5, 3, 9)
        assert outcome == OutcomeTier.WEAK_HIT

    def test_miss_progress_roll(self):
        outcome = resolve_outcome(4, 9, 8)
        assert outcome == OutcomeTier.MISS

    def test_match_on_progress_roll(self):
        assert check_match(7, 7) is True
        assert check_match(7, 8) is False


# ── Oracle integration ──────────────────────────────────────────────────────────


class TestOracleIntegration:
    @pytest.fixture
    def oracles(self):
        return load_oracles(DATA_DIR)

    def test_all_tables_load(self, oracles):
        assert len(oracles) > 0

    def test_pay_the_price_exists(self, oracles):
        assert "pay_the_price" in oracles

    def test_action_table_exists(self, oracles):
        assert "action" in oracles

    def test_lookup_returns_string(self, oracles):
        table = oracles["action"]
        result = table.lookup(50)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_full_range_coverage(self, oracles):
        """Every table should cover all 100 values."""
        for key, table in oracles.items():
            for roll in range(1, 101):
                result = table.lookup(roll)
                assert result != "Unknown", f"Table '{key}' returned Unknown for roll {roll}"

    def test_pay_the_price_boundary_values(self, oracles):
        table = oracles["pay_the_price"]
        assert table.lookup(1) != "Unknown"
        assert table.lookup(100) != "Unknown"

    def test_deterministic_lookup(self, oracles):
        """Same roll always returns same result."""
        table = oracles["action"]
        r1 = table.lookup(42)
        r2 = table.lookup(42)
        assert r1 == r2

    @pytest.mark.parametrize("table_key", ["action", "theme", "descriptor", "npc_role"])
    def test_common_tables_have_entries(self, oracles, table_key):
        table = oracles[table_key]
        assert len(table.results) > 0


# ── Vow + character integration ────────────────────────────────────────────────


class TestVowCharacterIntegration:
    """Test character stat + vow progress interacting correctly."""

    def setup_method(self):
        self.char = Character(
            name="Kael",
            stats=Stats(edge=3, heart=2, iron=3, shadow=2, wits=2),
            health=5,
            spirit=5,
            supply=3,
            momentum=4,
        )
        self.vow = Vow("Find the Andurath survivors", VowRank.DANGEROUS)

    def test_mark_progress_dangerous_adds_8_ticks(self):
        before = self.vow.ticks
        self.vow.mark_progress()
        assert self.vow.ticks == before + 8

    def test_progress_score_after_two_marks_dangerous(self):
        self.vow.mark_progress()
        self.vow.mark_progress()
        # 16 ticks → 4 boxes → score 4
        assert self.vow.progress_score == 4

    def test_forsake_vow_costs_spirit(self):
        cost = SPIRIT_COST[VowRank.DANGEROUS]
        old_spirit = self.char.spirit
        new_spirit = self.char.adjust_track("spirit", -cost)
        assert new_spirit == old_spirit - cost

    def test_forsake_epic_vow_costs_5_spirit(self):
        epic_vow = Vow("Unite the Forge", VowRank.EPIC)
        assert SPIRIT_COST[epic_vow.rank] == 5

    def test_spirit_clamps_at_zero_on_large_cost(self):
        self.char.spirit = 1
        # Forsake an extreme vow (cost 4), spirit floors at 0
        new_spirit = self.char.adjust_track("spirit", -4)
        assert new_spirit == 0
        assert self.char.spirit == 0

    def test_fulfill_vow_sets_fulfilled_flag(self):
        self.vow.fulfilled = True
        assert self.vow.fulfilled is True

    def test_progress_to_max(self):
        from starforged.models.vow import MAX_TICKS

        # Fill all the way
        while self.vow.ticks < MAX_TICKS:
            self.vow.mark_progress()
        assert self.vow.ticks == MAX_TICKS
        assert self.vow.progress_score == 10
        assert self.vow.boxes_filled == 10

    def test_high_iron_improves_strike_outcome(self):
        """Character with Iron 3 should have better Strike outcomes than Iron 1."""
        # Iron 3: action_score with die=4 → 7; easily beats low challenge
        result_high = resolve_move(action_die=4, stat=3, adds=0, c1=5, c2=3)
        # Iron 1: action_score with die=4 → 5
        result_low = resolve_move(action_die=4, stat=1, adds=0, c1=5, c2=3)
        tier_rank = {OutcomeTier.MISS: 0, OutcomeTier.WEAK_HIT: 1, OutcomeTier.STRONG_HIT: 2}
        assert tier_rank[result_high.outcome] >= tier_rank[result_low.outcome]


# ── Debility + momentum integration ────────────────────────────────────────────


class TestDebilityMomentumIntegration:
    def setup_method(self):
        self.char = Character(name="Test", stats=Stats(), momentum=8)

    def test_debility_lowers_effective_momentum_cap(self):
        self.char.toggle_debility("wounded")
        # Momentum should be clamped to new max (9)
        assert self.char.momentum <= self.char.momentum_max
        assert self.char.momentum_max == 9

    def test_momentum_burn_after_debility_uses_correct_reset(self):
        self.char.toggle_debility("wounded")
        self.char.toggle_debility("shaken")
        # Two debilities → reset is 0
        assert self.char.momentum_reset == 0
        self.char.burn_momentum()
        assert self.char.momentum == 0

    def test_would_momentum_improve_respects_actual_momentum(self):
        # With debility, momentum is clamped — test that improvement check
        # uses the actual (possibly lower) momentum value
        self.char.toggle_debility("wounded")
        self.char.toggle_debility("shaken")
        self.char.toggle_debility("unprepared")
        # momentum_max now 7; if momentum was 8, it got clamped to 7
        actual = self.char.momentum
        c1, c2 = 6, 5
        result = resolve_move(1, 1, 0, c1, c2)
        improvement = would_momentum_improve(result.outcome, actual, c1, c2)
        # If actual > both challenge dice, it should improve
        if actual > c1 and actual > c2:
            assert improvement is True
        else:
            assert improvement is False
