"""Tests for CharacterAsset model helpers (adjust_track, toggle_condition, serialisation)."""

from __future__ import annotations

from wyrd.models.asset import CharacterAsset


class TestAdjustTrack:
    def test_decrements_within_range(self):
        ca = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        result = ca.adjust_track("integrity", -2, 0, 5)
        assert result == 3
        assert ca.track_values["integrity"] == 3

    def test_increments_within_range(self):
        ca = CharacterAsset(asset_key="starship", track_values={"integrity": 2})
        result = ca.adjust_track("integrity", +2, 0, 5)
        assert result == 4
        assert ca.track_values["integrity"] == 4

    def test_clamps_at_min(self):
        ca = CharacterAsset(asset_key="starship", track_values={"integrity": 1})
        result = ca.adjust_track("integrity", -10, 0, 5)
        assert result == 0
        assert ca.track_values["integrity"] == 0

    def test_clamps_at_max(self):
        ca = CharacterAsset(asset_key="starship", track_values={"integrity": 4})
        result = ca.adjust_track("integrity", +10, 0, 5)
        assert result == 5
        assert ca.track_values["integrity"] == 5

    def test_defaults_to_max_when_track_not_set(self):
        ca = CharacterAsset(asset_key="starship")
        result = ca.adjust_track("integrity", -1, 0, 5)
        assert result == 4  # started at max (5), decremented by 1

    def test_exact_boundary_min(self):
        ca = CharacterAsset(asset_key="bot", track_values={"health": 0})
        result = ca.adjust_track("health", -1, 0, 5)
        assert result == 0

    def test_exact_boundary_max(self):
        ca = CharacterAsset(asset_key="bot", track_values={"health": 5})
        result = ca.adjust_track("health", +1, 0, 5)
        assert result == 5


class TestToggleCondition:
    def test_toggle_on(self):
        ca = CharacterAsset(asset_key="starship")
        result = ca.toggle_condition("battered")
        assert result is True
        assert "battered" in ca.conditions

    def test_toggle_off(self):
        ca = CharacterAsset(asset_key="starship", conditions={"battered"})
        result = ca.toggle_condition("battered")
        assert result is False
        assert "battered" not in ca.conditions

    def test_toggle_on_then_off(self):
        ca = CharacterAsset(asset_key="starship")
        ca.toggle_condition("cursed")
        ca.toggle_condition("cursed")
        assert "cursed" not in ca.conditions

    def test_condition_stored_lowercase(self):
        ca = CharacterAsset(asset_key="starship")
        ca.toggle_condition("BATTERED")
        assert "battered" in ca.conditions

    def test_multiple_conditions(self):
        ca = CharacterAsset(asset_key="starship")
        ca.toggle_condition("battered")
        ca.toggle_condition("cursed")
        assert "battered" in ca.conditions
        assert "cursed" in ca.conditions


class TestSerialisationRoundTrip:
    def test_to_dict_includes_conditions(self):
        ca = CharacterAsset(
            asset_key="starship",
            track_values={"integrity": 3},
            conditions={"battered"},
        )
        data = ca.to_dict()
        assert data["conditions"] == ["battered"]  # sorted list

    def test_to_dict_conditions_sorted(self):
        ca = CharacterAsset(asset_key="starship", conditions={"cursed", "battered"})
        data = ca.to_dict()
        assert data["conditions"] == ["battered", "cursed"]

    def test_round_trip_with_conditions(self):
        ca = CharacterAsset(
            asset_key="starship",
            abilities_unlocked=[True, False, False],
            track_values={"integrity": 3},
            input_values={"name": "Rust Runner"},
            conditions={"battered"},
        )
        data = ca.to_dict()
        restored = CharacterAsset.from_dict(data)
        assert restored.asset_key == "starship"
        assert restored.abilities_unlocked == [True, False, False]
        assert restored.track_values == {"integrity": 3}
        assert restored.input_values == {"name": "Rust Runner"}
        assert restored.conditions == {"battered"}

    def test_from_dict_missing_conditions_defaults_to_empty(self):
        """Old saves without 'conditions' key load cleanly."""
        old_data = {
            "asset_key": "starship",
            "abilities_unlocked": [True, False, False],
            "track_values": {"integrity": 5},
            "input_values": {},
        }
        ca = CharacterAsset.from_dict(old_data)
        assert ca.conditions == set()

    def test_from_dict_string_format(self):
        """Old saves with assets as bare strings load cleanly."""
        ca = CharacterAsset.from_dict("navigator")
        assert ca.asset_key == "navigator"
        assert ca.conditions == set()
        assert ca.track_values == {}
