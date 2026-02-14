"""Tests for the Character model."""

from soloquest.models.character import (
    MOMENTUM_MAX_BASE,
    MOMENTUM_RESET_BASE,
    Character,
    Stats,
)


class TestStats:
    def test_get_by_name(self):
        s = Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        assert s.get("edge") == 2
        assert s.get("IRON") == 3

    def test_as_dict(self):
        s = Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        d = s.as_dict()
        assert d == {"edge": 2, "heart": 1, "iron": 3, "shadow": 2, "wits": 3}


class TestCharacter:
    def setup_method(self):
        self.char = Character(
            name="Kael",
            homeworld="Drift Station",
            stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3),
        )

    def test_adjust_track_up(self):
        self.char.health = 3
        new = self.char.adjust_track("health", 2)
        assert new == 5
        assert self.char.health == 5

    def test_adjust_track_clamps_at_5(self):
        self.char.health = 5
        new = self.char.adjust_track("health", 2)
        assert new == 5

    def test_adjust_track_clamps_at_0(self):
        self.char.health = 1
        new = self.char.adjust_track("health", -5)
        assert new == 0

    def test_adjust_momentum(self):
        self.char.momentum = 2
        new = self.char.adjust_momentum(3)
        assert new == 5
        assert self.char.momentum == 5

    def test_adjust_momentum_max_cap(self):
        self.char.momentum = 9
        new = self.char.adjust_momentum(5)
        assert new == MOMENTUM_MAX_BASE  # 10

    def test_adjust_momentum_min_cap(self):
        self.char.momentum = -4
        new = self.char.adjust_momentum(-5)
        assert new == -6

    def test_burn_momentum_resets(self):
        self.char.momentum = 7
        old = self.char.burn_momentum()
        assert old == 7
        assert self.char.momentum == self.char.momentum_reset

    def test_serialization_roundtrip(self):
        data = self.char.to_dict()
        restored = Character.from_dict(data)
        assert restored.name == self.char.name
        assert restored.stats.iron == self.char.stats.iron
        assert restored.health == self.char.health


class TestDebilities:
    def setup_method(self):
        self.char = Character(name="Test", stats=Stats())

    def test_no_debilities_default_momentum_max(self):
        assert self.char.momentum_max == MOMENTUM_MAX_BASE

    def test_no_debilities_default_momentum_reset(self):
        assert self.char.momentum_reset == MOMENTUM_RESET_BASE

    def test_one_debility_reduces_max_by_1(self):
        self.char.toggle_debility("wounded")
        assert self.char.momentum_max == MOMENTUM_MAX_BASE - 1

    def test_one_debility_does_not_change_reset(self):
        self.char.toggle_debility("wounded")
        assert self.char.momentum_reset == MOMENTUM_RESET_BASE

    def test_two_debilities_reset_drops_to_zero(self):
        self.char.toggle_debility("wounded")
        self.char.toggle_debility("shaken")
        assert self.char.momentum_reset == 0

    def test_two_debilities_reduce_max_by_2(self):
        self.char.toggle_debility("wounded")
        self.char.toggle_debility("shaken")
        assert self.char.momentum_max == MOMENTUM_MAX_BASE - 2

    def test_toggle_off_removes_debility(self):
        self.char.toggle_debility("wounded")
        now_active = self.char.toggle_debility("wounded")
        assert now_active is False
        assert "wounded" not in self.char.debilities

    def test_toggle_returns_true_when_added(self):
        result = self.char.toggle_debility("shaken")
        assert result is True

    def test_toggle_returns_false_when_removed(self):
        self.char.toggle_debility("shaken")
        result = self.char.toggle_debility("shaken")
        assert result is False

    def test_momentum_clamped_when_debility_added(self):
        # If momentum is at max, adding a debility should clamp it down
        self.char.momentum = MOMENTUM_MAX_BASE  # 10
        self.char.toggle_debility("wounded")
        assert self.char.momentum <= self.char.momentum_max

    def test_all_six_debilities_reduce_max_by_6(self):
        for d in ["wounded", "shaken", "unprepared", "encumbered", "maimed", "corrupted"]:
            self.char.toggle_debility(d)
        assert self.char.momentum_max == MOMENTUM_MAX_BASE - 6

    def test_serialization_preserves_debilities(self):
        self.char.toggle_debility("wounded")
        self.char.toggle_debility("shaken")
        data = self.char.to_dict()
        restored = Character.from_dict(data)
        assert "wounded" in restored.debilities
        assert "shaken" in restored.debilities
        assert restored.momentum_max == MOMENTUM_MAX_BASE - 2
        assert restored.momentum_reset == 0

    def test_invalid_debility_returns_none(self):
        """Invalid debility names return None instead of raising."""
        result = self.char.toggle_debility("invincible")
        assert result is None
        assert "invincible" not in self.char.debilities

    def test_invalid_stat_name_raises(self):
        """Stats.get raises ValueError for invalid stat names."""
        import pytest

        stats = Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        with pytest.raises(ValueError, match="Invalid stat name"):
            stats.get("invalid_stat")
