"""Tests for the Character model."""

from wyrd.models.character import (
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

    def test_serialization_with_assets(self):
        """Regression: Character.to_dict() should work with CharacterAsset objects.

        Bug: Character creation added assets as strings, but to_dict() expected
        CharacterAsset objects with .asset_key attribute. This caused AttributeError
        when calling /end command to save the character.

        Fixed in: main.py - convert asset key strings to CharacterAsset objects
        during character creation.
        """
        from wyrd.models.asset import CharacterAsset

        # Simulate character creation with assets (as CharacterAsset objects)
        self.char.assets = [
            CharacterAsset(asset_key="starship"),
            CharacterAsset(asset_key="navigator"),
            CharacterAsset(asset_key="ace"),
        ]

        # This should not raise AttributeError: 'str' object has no attribute 'asset_key'
        try:
            data = self.char.to_dict()
        except AttributeError as e:
            if "has no attribute 'asset_key'" in str(e):
                raise AssertionError(
                    "Regression: to_dict() failed because assets are strings instead of CharacterAsset objects"
                ) from e
            raise

        # Verify serialization is correct
        assert "assets" in data
        assert len(data["assets"]) == 3
        assert all(isinstance(a, dict) for a in data["assets"])
        assert data["assets"][0]["asset_key"] == "starship"
        assert data["assets"][1]["asset_key"] == "navigator"
        assert data["assets"][2]["asset_key"] == "ace"

        # Verify deserialization works
        restored = Character.from_dict(data)
        assert len(restored.assets) == 3
        assert all(hasattr(a, "asset_key") for a in restored.assets)
        assert restored.assets[0].asset_key == "starship"

    def test_character_sheet_display_with_assets(self):
        """Regression: Character sheet should display correctly with CharacterAsset objects.

        Bug: Previously tried to call .replace() on CharacterAsset object instead of asset_key.
        """
        from wyrd.models.asset import CharacterAsset
        from wyrd.ui.display import character_sheet

        # Add assets to character
        self.char.assets = [
            CharacterAsset(asset_key="starship", abilities_unlocked=[True, False, False]),
            CharacterAsset(asset_key="navigator", abilities_unlocked=[True]),
        ]

        # This should not raise an AttributeError
        try:
            character_sheet(self.char, vows=[], session_count=1)
            # If we get here without exception, the test passes
        except AttributeError as e:
            # If we get AttributeError about 'replace', the bug is present
            if "'CharacterAsset' object has no attribute 'replace'" in str(e):
                raise AssertionError(
                    "Character sheet display bug: trying to call .replace() on CharacterAsset object"
                ) from e
            raise

    def test_character_sheet_display_empty_assets(self):
        """Character sheet should handle empty asset list correctly."""
        from wyrd.ui.display import character_sheet

        # Empty assets list
        self.char.assets = []

        # Should not crash
        try:
            character_sheet(self.char, vows=[], session_count=1)
        except Exception as e:
            raise AssertionError(f"Character sheet crashed with empty assets: {e}") from e

    def test_character_sheet_display_asset_with_underscores(self):
        """Asset keys with underscores should be formatted correctly for display."""
        from wyrd.models.asset import CharacterAsset
        from wyrd.ui.display import character_sheet

        # Asset with underscores in key
        self.char.assets = [
            CharacterAsset(asset_key="engine_upgrade", abilities_unlocked=[True]),
        ]

        # Should not crash and should format the name correctly
        try:
            character_sheet(self.char, vows=[], session_count=1)
        except Exception as e:
            raise AssertionError(
                f"Character sheet crashed with underscore in asset key: {e}"
            ) from e


class TestCharacterNarrativeFields:
    def test_supply_default_is_5(self):
        char = Character(name="Test")
        assert char.supply == 5

    def test_new_fields_default_to_empty(self):
        char = Character(name="Test")
        assert char.pronouns == ""
        assert char.callsign == ""
        assert char.backstory == ""
        assert char.look == ""
        assert char.act == ""
        assert char.wear == ""
        assert char.gear == []

    def test_new_fields_serialized_in_to_dict(self):
        char = Character(
            name="Kael",
            pronouns="they/them",
            callsign="Ghost",
            backstory="Fled the war.",
            look="Tall, scarred",
            act="Calm under pressure",
            wear="Worn flight jacket",
            gear=["data pad", "lucky coin"],
        )
        data = char.to_dict()
        assert data["pronouns"] == "they/them"
        assert data["callsign"] == "Ghost"
        assert data["backstory"] == "Fled the war."
        assert data["look"] == "Tall, scarred"
        assert data["act"] == "Calm under pressure"
        assert data["wear"] == "Worn flight jacket"
        assert data["gear"] == ["data pad", "lucky coin"]

    def test_new_fields_roundtrip(self):
        char = Character(
            name="Kael",
            pronouns="she/her",
            callsign="Ace",
            backstory="Origin story.",
            look="Short hair",
            act="Bold",
            wear="Armour",
            gear=["knife"],
        )
        restored = Character.from_dict(char.to_dict())
        assert restored.pronouns == "she/her"
        assert restored.callsign == "Ace"
        assert restored.backstory == "Origin story."
        assert restored.look == "Short hair"
        assert restored.act == "Bold"
        assert restored.wear == "Armour"
        assert restored.gear == ["knife"]

    def test_old_saves_load_with_empty_defaults(self):
        """Existing saves without new fields load with empty/default values."""
        old_data = {
            "name": "OldChar",
            "homeworld": "Sol",
            "stats": {"edge": 2, "heart": 2, "iron": 1, "shadow": 2, "wits": 3},
            "health": 5,
            "spirit": 5,
            "supply": 3,
            "momentum": 2,
            "debilities": [],
            "assets": [],
            "truths": [],
        }
        char = Character.from_dict(old_data)
        assert char.pronouns == ""
        assert char.callsign == ""
        assert char.backstory == ""
        assert char.look == ""
        assert char.act == ""
        assert char.wear == ""
        assert char.gear == []
        # Old supply value preserved (not overridden)
        assert char.supply == 3


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
