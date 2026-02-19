"""Tests for the /asset command handler (meter and condition mutations)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from soloquest.commands.asset import handle_asset
from soloquest.models.asset import Asset, AssetAbility, CharacterAsset
from soloquest.models.character import Character, Stats
from soloquest.models.session import EntryKind, Session


def _make_state(char_assets: list[CharacterAsset], asset_defs: dict[str, Asset]) -> MagicMock:
    state = MagicMock()
    state.character = Character(name="Tester", stats=Stats())
    state.character.assets = char_assets
    state.assets = asset_defs
    state.session = Session(number=1)
    return state


def _starship_def() -> Asset:
    return Asset(
        key="starship",
        name="Starship",
        category="command_vehicle",
        tracks={"integrity": (0, 5)},
        abilities=[AssetAbility(text="Ability one")],
    )


def _bot_def() -> Asset:
    return Asset(
        key="combat_bot",
        name="Combat Bot",
        category="companion",
        tracks={"health": (0, 5)},
    )


def _no_track_def() -> Asset:
    return Asset(
        key="navigator",
        name="Navigator",
        category="path",
        tracks={},
    )


class TestUpdatePrimaryMeter:
    def test_decrement_primary_meter(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "-1"], set())

        assert char_asset.track_values["integrity"] == 4

    def test_increment_primary_meter(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 3})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "+2"], set())

        assert char_asset.track_values["integrity"] == 5

    def test_clamped_at_min(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 1})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "-10"], set())

        assert char_asset.track_values["integrity"] == 0

    def test_change_logged_to_session(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "-1"], set())

        mech_entries = [e for e in state.session.entries if e.kind == EntryKind.MECHANICAL]
        assert len(mech_entries) == 1
        assert "Integrity" in mech_entries[0].text
        assert "Starship" in mech_entries[0].text


class TestUpdateNamedMeter:
    def test_update_named_meter(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "integrity", "-1"], set())

        assert char_asset.track_values["integrity"] == 4

    def test_named_meter_logged(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "integrity", "-2"], set())

        mech_entries = [e for e in state.session.entries if e.kind == EntryKind.MECHANICAL]
        assert len(mech_entries) == 1

    @patch("soloquest.commands.asset.display.error")
    def test_invalid_meter_name_shows_error(self, mock_error):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "shields", "-1"], set())

        mock_error.assert_called_once()
        assert char_asset.track_values.get("shields") is None


class TestToggleCondition:
    def test_toggle_condition_on(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "battered"], set())

        assert "battered" in char_asset.conditions

    def test_toggle_condition_off(self):
        char_asset = CharacterAsset(
            asset_key="starship",
            track_values={"integrity": 5},
            conditions={"battered"},
        )
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "battered"], set())

        assert "battered" not in char_asset.conditions

    def test_condition_logged_to_session(self):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["starship", "battered"], set())

        mech_entries = [e for e in state.session.entries if e.kind == EntryKind.MECHANICAL]
        assert len(mech_entries) == 1
        assert "Battered" in mech_entries[0].text


class TestErrorCases:
    @patch("soloquest.commands.asset.display.error")
    def test_unknown_asset_shows_error(self, mock_error):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state([char_asset], {"starship": _starship_def()})

        handle_asset(state, ["xyzunknown", "-1"], set())

        mock_error.assert_called()

    @patch("soloquest.commands.asset.display.error")
    def test_asset_with_no_meter_errors(self, mock_error):
        char_asset = CharacterAsset(asset_key="navigator")
        state = _make_state([char_asset], {"navigator": _no_track_def()})

        handle_asset(state, ["navigator", "-1"], set())

        mock_error.assert_called_once()
        assert "no condition meters" in mock_error.call_args[0][0].lower()

    @patch("soloquest.commands.asset.display.error")
    def test_mutation_on_unowned_asset_errors(self, mock_error):
        char_asset = CharacterAsset(asset_key="starship", track_values={"integrity": 5})
        state = _make_state(
            [char_asset],
            {"starship": _starship_def(), "combat_bot": _bot_def()},
        )

        # Character doesn't own combat_bot
        handle_asset(state, ["combat_bot", "-1"], set())

        mock_error.assert_called()


class TestNoArgs:
    @patch("soloquest.commands.asset.display.console")
    def test_no_args_lists_assets(self, mock_console):
        state = _make_state([], {"starship": _starship_def()})

        handle_asset(state, [], set())

        # Should call console.print (listing assets)
        mock_console.print.assert_called()
