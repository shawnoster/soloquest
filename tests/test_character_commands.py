"""Tests for character command handlers."""

from unittest.mock import MagicMock, patch

from soloquest.commands.character import (
    handle_char,
    handle_momentum,
    handle_settings,
    handle_track,
)
from soloquest.engine.dice import DiceMode
from soloquest.models.character import Character, Stats
from soloquest.models.session import Session


class TestHandleChar:
    """Tests for /char command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test Character", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.vows = []
        self.state.session_count = 5
        self.state.dice_mode = DiceMode("digital")

    @patch("soloquest.commands.character.display.character_sheet")
    def test_handle_char_displays_character_sheet(self, mock_display):
        """handle_char should call display.character_sheet with correct parameters."""
        handle_char(self.state, [], set())

        mock_display.assert_called_once_with(
            self.state.character,
            self.state.vows,
            session_count=5,
            assets=self.state.assets,
        )


class TestHandleTrack:
    """Tests for /health, /spirit, /supply commands."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.character.health = 3
        self.state.character.spirit = 4
        self.state.character.supply = 5
        self.state.session = Session(number=1)

    @patch("soloquest.commands.character.display.info")
    def test_handle_track_no_args_shows_current_value(self, mock_info):
        """handle_track with no args should display current track value."""
        handle_track(self.state, "health", [])

        mock_info.assert_called_once()
        call_args = mock_info.call_args[0][0]
        assert "Health" in call_args
        assert "3/5" in call_args

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_track_positive_delta(self, mock_display):
        """handle_track should increase track value with positive delta."""
        handle_track(self.state, "health", ["+2"])

        assert self.state.character.health == 5  # 3 + 2
        mock_display.assert_called_once()
        call_args = mock_display.call_args[0][0]
        assert call_args == "Health +2 → 5/5"

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_track_negative_delta(self, mock_display):
        """handle_track should decrease track value with negative delta."""
        handle_track(self.state, "spirit", ["-2"])

        assert self.state.character.spirit == 2  # 4 - 2
        mock_display.assert_called_once()
        call_args = mock_display.call_args[0][0]
        assert call_args == "Spirit -2 → 2/5"

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_track_logs_to_session(self, mock_display):
        """handle_track should log changes to session."""
        handle_track(self.state, "supply", ["+1"])

        # Check session log
        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "Supply +1" in entry.text
        assert entry.kind == "mechanical"

    @patch("soloquest.commands.character.display.error")
    def test_handle_track_invalid_value_shows_error(self, mock_error):
        """handle_track with invalid value should show error."""
        handle_track(self.state, "health", ["notanumber"])

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "Usage" in call_args

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_track_works_with_all_tracks(self, mock_display):
        """handle_track should work with health, spirit, and supply."""
        for track in ["health", "spirit", "supply"]:
            mock_display.reset_mock()
            handle_track(self.state, track, ["+1"])
            mock_display.assert_called_once()


class TestHandleMomentum:
    """Tests for /momentum command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.character.momentum = 0
        self.state.session = Session(number=1)

    @patch("soloquest.commands.character.display.info")
    def test_handle_momentum_no_args_shows_current_value(self, mock_info):
        """handle_momentum with no args should display current momentum."""
        self.state.character.momentum = 5
        handle_momentum(self.state, [], set())

        mock_info.assert_called_once()
        call_args = mock_info.call_args[0][0]
        assert "Momentum" in call_args
        assert "+5" in call_args

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_momentum_positive_delta(self, mock_update):
        """handle_momentum should increase momentum with positive delta."""
        self.state.character.momentum = 2
        handle_momentum(self.state, ["+3"], set())

        assert self.state.character.momentum == 5
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0][0]
        assert call_args == "Momentum +3 → +5"

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_momentum_negative_delta(self, mock_update):
        """handle_momentum should decrease momentum with negative delta."""
        self.state.character.momentum = 5
        handle_momentum(self.state, ["-3"], set())

        assert self.state.character.momentum == 2
        mock_update.assert_called_once()
        call_args = mock_update.call_args[0][0]
        assert call_args == "Momentum -3 → +2"

    @patch("soloquest.commands.character.display.mechanical_update")
    def test_handle_momentum_logs_to_session(self, mock_update):
        """handle_momentum should log changes to session."""
        handle_momentum(self.state, ["+2"], set())

        # Check session log
        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "Momentum +2" in entry.text
        assert entry.kind == "mechanical"

    @patch("soloquest.commands.character.display.error")
    def test_handle_momentum_invalid_value_shows_error(self, mock_error):
        """handle_momentum with invalid value should show error."""
        handle_momentum(self.state, ["notanumber"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "Usage" in call_args


class TestHandleSettings:
    """Tests for /settings command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(name="Test", stats=Stats())
        self.state.dice_mode = DiceMode("digital")
        self.state.session = Session(number=1)

    @patch("soloquest.commands.character.display.info")
    def test_handle_settings_no_args_shows_current_settings(self, mock_info):
        """handle_settings with no args should display current settings."""
        handle_settings(self.state, [], set())

        # Should be called three times: adventures dir, dice mode, usage
        assert mock_info.call_count == 3
        calls = [call[0][0] for call in mock_info.call_args_list]
        assert any("Adventures directory" in call for call in calls)
        assert any("Dice mode: digital" in call for call in calls)
        assert any("Usage" in call for call in calls)

    @patch("soloquest.commands.character.display.success")
    @patch("soloquest.commands.character.make_dice_provider")
    def test_handle_settings_change_dice_mode(self, mock_make_dice, mock_success):
        """handle_settings should change dice mode."""
        mock_dice = MagicMock()
        mock_make_dice.return_value = mock_dice

        handle_settings(self.state, ["dice", "physical"], set())

        assert self.state.dice_mode == DiceMode("physical")
        assert self.state.dice == mock_dice
        mock_success.assert_called_once()
        call_args = mock_success.call_args[0][0]
        assert "physical" in call_args

    @patch("soloquest.commands.character.display.success")
    @patch("soloquest.commands.character.make_dice_provider")
    def test_handle_settings_change_to_mixed_mode(self, mock_make_dice, mock_success):
        """handle_settings should support mixed dice mode."""
        mock_dice = MagicMock()
        mock_make_dice.return_value = mock_dice

        handle_settings(self.state, ["dice", "mixed"], set())

        assert self.state.dice_mode == DiceMode("mixed")
        mock_success.assert_called_once()

    @patch("soloquest.commands.character.display.success")
    @patch("soloquest.commands.character.make_dice_provider")
    def test_handle_settings_logs_to_session(self, mock_make_dice, mock_success):
        """handle_settings should log dice mode changes to session."""
        mock_make_dice.return_value = MagicMock()

        handle_settings(self.state, ["dice", "physical"], set())

        # Check session log
        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert "Dice mode changed to physical" in entry.text
        assert entry.kind == "mechanical"

    @patch("soloquest.commands.character.display.error")
    def test_handle_settings_invalid_mode_shows_error(self, mock_error):
        """handle_settings with invalid dice mode should show error."""
        handle_settings(self.state, ["dice", "invalid"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "Unknown dice mode" in call_args

    @patch("soloquest.commands.character.display.error")
    def test_handle_settings_missing_mode_shows_error(self, mock_error):
        """handle_settings with dice but no mode should show error."""
        handle_settings(self.state, ["dice"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "Usage" in call_args

    @patch("soloquest.commands.character.display.error")
    def test_handle_settings_unknown_setting_shows_error(self, mock_error):
        """handle_settings with unknown setting should show error."""
        handle_settings(self.state, ["unknown", "value"], set())

        mock_error.assert_called_once()
        call_args = mock_error.call_args[0][0]
        assert "Usage" in call_args

    @patch("soloquest.commands.character.display.success")
    @patch("soloquest.commands.character.make_dice_provider")
    def test_handle_settings_case_insensitive(self, mock_make_dice, mock_success):
        """handle_settings should handle uppercase dice mode names."""
        mock_make_dice.return_value = MagicMock()

        handle_settings(self.state, ["dice", "PHYSICAL"], set())

        assert self.state.dice_mode == DiceMode("physical")


class TestHandleCharNew:
    """Tests for /char new subcommand."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Old Character", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.vows = []
        self.state.session_count = 5
        self.state.dice_mode = DiceMode("digital")
        self.state.truth_categories = {}

    @patch("soloquest.commands.character.display.character_sheet")
    def test_no_args_shows_character_sheet(self, mock_sheet):
        """handle_char with no args still shows character sheet."""
        handle_char(self.state, [], set())

        mock_sheet.assert_called_once()

    @patch("soloquest.commands.character.display.info")
    @patch("soloquest.commands.character.Confirm.ask", return_value=False)
    def test_char_new_deny_returns_early(self, mock_confirm, mock_info):
        """Declining the confirmation guard returns without creating a character."""
        handle_char(self.state, ["new"], set())

        mock_info.assert_called()
        # State should be unchanged
        assert self.state.character.name == "Old Character"

    @patch("soloquest.commands.character.display.info")
    @patch("soloquest.commands.character.display.warn")
    @patch("soloquest.commands.character.Confirm.ask", side_effect=KeyboardInterrupt)
    def test_char_new_keyboard_interrupt_returns_early(self, mock_confirm, mock_warn, mock_info):
        """KeyboardInterrupt at confirmation returns without creating a character."""
        handle_char(self.state, ["new"], set())

        assert self.state.character.name == "Old Character"

    @patch("soloquest.commands.character.save_game")
    @patch("soloquest.commands.character.make_dice_provider")
    @patch("soloquest.commands.character.display.success")
    @patch("soloquest.commands.character.display.warn")
    @patch("soloquest.commands.character.Confirm.ask", return_value=True)
    def test_char_new_updates_state_on_success(
        self, mock_confirm, mock_warn, mock_success, mock_make_dice, mock_save
    ):
        """Successful /char new updates state in-place with new character."""
        from soloquest.models.character import Character, Stats
        from soloquest.models.vow import Vow

        new_char = Character(name="New Hero", stats=Stats())
        from soloquest.models.vow import VowRank

        new_vows = [Vow(description="A new vow", rank=VowRank.EPIC)]
        mock_make_dice.return_value = MagicMock()

        with patch(
            "soloquest.commands.character.run_new_character_flow",
            return_value=(new_char, new_vows, DiceMode.DIGITAL),
        ):
            handle_char(self.state, ["new"], set())

        assert self.state.character == new_char
        assert self.state.vows == new_vows
        assert self.state.session_count == 0
        assert self.state.session is None
        mock_save.assert_called_once()
        mock_success.assert_called_once()

    @patch("soloquest.commands.character.display.info")
    @patch("soloquest.commands.character.Confirm.ask", return_value=True)
    def test_char_new_cancelled_flow_shows_info(self, mock_confirm, mock_info):
        """Cancelling during new character flow shows info message."""
        with patch(
            "soloquest.commands.character.run_new_character_flow",
            return_value=None,
        ):
            handle_char(self.state, ["new"], set())

        mock_info.assert_called()
        # State unchanged
        assert self.state.character.name == "Old Character"
