"""Tests for session command handlers."""

from unittest.mock import MagicMock, call, patch

from soloquest.commands.session import handle_end, handle_help, handle_log, handle_newsession, handle_note
from soloquest.engine.dice import DiceMode
from soloquest.models.character import Character, Stats
from soloquest.models.session import EntryKind, LogEntry, Session
from soloquest.models.vow import Vow, VowRank


class TestHandleLog:
    """Tests for /log command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test Character", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.session = Session(number=1)

    @patch("soloquest.commands.session.display")
    def test_empty_session_shows_message(self, mock_display):
        """handle_log with no entries should show info message."""
        handle_log(self.state, [], set())

        mock_display.info.assert_called_once_with("No entries in this session yet.")

    @patch("soloquest.commands.session.display")
    def test_displays_all_entries(self, mock_display):
        """handle_log should display all entries by default."""
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="First entry"),
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
            LogEntry(kind=EntryKind.ORACLE, text="Action: Attack"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Health +1"),
        ]

        handle_log(self.state, [], set())

        mock_display.rule.assert_called_once_with("Session 1 Log")
        assert mock_display.log_entry.call_count == 4

    @patch("soloquest.commands.session.display")
    def test_moves_flag_shows_only_moves_and_oracles(self, mock_display):
        """handle_log with --moves flag should show only move and oracle entries."""
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Journal entry"),
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
            LogEntry(kind=EntryKind.ORACLE, text="Action: Attack"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Health +1"),
            LogEntry(kind=EntryKind.NOTE, text="NPC note"),
        ]

        handle_log(self.state, [], {"moves"})

        assert mock_display.log_entry.call_count == 2
        kinds_shown = [call[0][0].kind for call in mock_display.log_entry.call_args_list]
        assert EntryKind.MOVE in kinds_shown
        assert EntryKind.ORACLE in kinds_shown

    @patch("soloquest.commands.session.display")
    def test_compact_flag_skips_mechanical(self, mock_display):
        """handle_log with --compact flag should skip mechanical entries."""
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Journal entry"),
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Health +1"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Momentum +2"),
        ]

        handle_log(self.state, [], {"compact"})

        assert mock_display.log_entry.call_count == 2
        kinds_shown = [call[0][0].kind for call in mock_display.log_entry.call_args_list]
        assert EntryKind.MECHANICAL not in kinds_shown

    @patch("soloquest.commands.session.display")
    def test_moves_and_compact_flags_together(self, mock_display):
        """handle_log with both flags should apply both filters."""
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Journal"),
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
            LogEntry(kind=EntryKind.ORACLE, text="Action"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Health +1"),
        ]

        handle_log(self.state, [], {"moves", "compact"})

        assert mock_display.log_entry.call_count == 2
        kinds_shown = [call[0][0].kind for call in mock_display.log_entry.call_args_list]
        assert EntryKind.MOVE in kinds_shown
        assert EntryKind.ORACLE in kinds_shown

    @patch("soloquest.commands.session.display")
    def test_empty_entries_with_moves_flag(self, mock_display):
        """handle_log with --moves flag but no moves/oracles should show empty."""
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Journal"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Health +1"),
        ]

        handle_log(self.state, [], {"moves"})

        mock_display.log_entry.assert_not_called()


class TestHandleNote:
    """Tests for /note command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Test Character", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.session = Session(number=1)

    @patch("soloquest.commands.session.display")
    def test_note_without_args_shows_error(self, mock_display):
        """handle_note with no args should show usage error."""
        handle_note(self.state, [], set())

        mock_display.error.assert_called_once()
        call_args = mock_display.error.call_args[0][0]
        assert "Usage" in call_args

    @patch("soloquest.commands.session.display")
    def test_note_adds_to_session(self, mock_display):
        """handle_note should add note to session."""
        handle_note(self.state, ["Remember", "the", "store"], set())

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert entry.kind == EntryKind.NOTE
        assert entry.text == "Remember the store"

    @patch("soloquest.commands.session.display")
    def test_note_displays_success(self, mock_display):
        """handle_note should display success message."""
        handle_note(self.state, ["Test note"], set())

        mock_display.success.assert_called_once()
        call_args = mock_display.success.call_args[0][0]
        assert "Test note" in call_args

    @patch("soloquest.commands.session.display")
    def test_note_with_special_characters(self, mock_display):
        """handle_note should handle special characters correctly."""
        handle_note(self.state, ["NPC:", "Kael's", "brother", "(wounded)"], set())

        assert len(self.state.session.entries) == 1
        entry = self.state.session.entries[0]
        assert entry.text == "NPC: Kael's brother (wounded)"
        assert entry.kind == EntryKind.NOTE

    @patch("soloquest.commands.session.display")
    def test_note_with_single_word(self, mock_display):
        """handle_note should handle single word notes."""
        handle_note(self.state, ["ambush!"], set())

        assert len(self.state.session.entries) == 1
        assert self.state.session.entries[0].text == "ambush!"


class TestHandleNewsession:
    """Tests for /newsession command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Kael", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.session = Session(number=1)
        self.state.session_count = 1
        self.state.vows = []
        self.state.dice_mode = DiceMode.DIGITAL

    @patch("soloquest.commands.session.display")
    @patch("rich.prompt.Confirm.ask", return_value=True)
    @patch("soloquest.commands.session._export_session")
    @patch("soloquest.state.save.save_game", return_value="/tmp/save.json")
    def test_newsession_with_entries_confirms_and_exports(
        self, mock_save, mock_export, mock_confirm, mock_display
    ):
        """handle_newsession with entries should confirm, export, and create new session."""
        # Add entries to current session
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Test entry"),
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
        ]

        handle_newsession(self.state, [], set())

        # Should show confirmation dialog
        mock_display.rule.assert_called_with("Start New Session")
        mock_display.warn.assert_called()
        mock_confirm.assert_called_once()

        # Should export old session
        mock_export.assert_called_once_with(self.state)

        # Should increment session count
        assert self.state.session_count == 2

        # Should create new session
        assert self.state.session.number == 2
        assert len(self.state.session.entries) == 0

        # Should save game
        mock_save.assert_called_once()

    @patch("soloquest.commands.session.display")
    @patch("rich.prompt.Confirm.ask", return_value=False)
    @patch("soloquest.commands.session._export_session")
    def test_newsession_cancelled_by_user(self, mock_export, mock_confirm, mock_display):
        """handle_newsession should cancel if user declines confirmation."""
        self.state.session.entries = [LogEntry(kind=EntryKind.JOURNAL, text="Test")]

        handle_newsession(self.state, [], set())

        # Should confirm
        mock_confirm.assert_called_once()

        # Should not export or change session
        mock_export.assert_not_called()
        assert self.state.session_count == 1
        assert len(self.state.session.entries) == 1

    @patch("soloquest.commands.session.display")
    @patch("soloquest.state.save.save_game", return_value="/tmp/save.json")
    def test_newsession_without_entries_no_confirmation(self, mock_save, mock_display):
        """handle_newsession without entries should not show confirmation."""
        # Empty session
        assert len(self.state.session.entries) == 0

        handle_newsession(self.state, [], set())

        # Should not show confirmation dialog (rule not called for empty session)
        # Should create new session immediately
        assert self.state.session_count == 2
        assert self.state.session.number == 2

    @patch("soloquest.commands.session.display")
    @patch("rich.prompt.Confirm.ask", return_value=True)
    @patch("soloquest.commands.session._export_session")
    @patch("soloquest.state.save.save_game", return_value="/tmp/save.json")
    def test_newsession_increments_session_number_correctly(
        self, mock_save, mock_export, mock_confirm, mock_display
    ):
        """handle_newsession should increment session number correctly."""
        self.state.session.entries = [LogEntry(kind=EntryKind.JOURNAL, text="Entry")]
        self.state.session_count = 5

        handle_newsession(self.state, [], set())

        assert self.state.session_count == 6
        assert self.state.session.number == 6


class TestHandleEnd:
    """Tests for /end command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Kael", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        self.state.character.momentum = 3
        self.state.session = Session(number=1)
        self.state.session_count = 1
        self.state.vows = []
        self.state.dice_mode = DiceMode.DIGITAL
        self.state.running = True

    @patch("soloquest.commands.session.display")
    @patch("soloquest.commands.session.Prompt.ask", return_value="Epic Session")
    @patch("soloquest.commands.session._export_session")
    @patch("soloquest.commands.session.save_game", return_value="/tmp/save.json")
    def test_end_with_entries_and_title(self, mock_save, mock_export, mock_prompt, mock_display):
        """handle_end with entries should prompt for title and export."""
        # Add various entry types
        self.state.session.entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Story entry"),
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
            LogEntry(kind=EntryKind.ORACLE, text="Action: Attack"),
            LogEntry(kind=EntryKind.NOTE, text="NPC note"),
        ]

        handle_end(self.state, [], set())

        # Should prompt for title
        mock_prompt.assert_called_once()
        assert self.state.session.title == "Epic Session"

        # Should display stats
        mock_display.rule.assert_called_with("End Session")
        info_calls = [call[0][0] for call in mock_display.info.call_args_list]
        assert any("Moves rolled:" in call for call in info_calls)
        assert any("Oracles consulted:" in call for call in info_calls)
        assert any("Journal entries:" in call for call in info_calls)
        assert any("Notes:" in call for call in info_calls)

        # Should export session
        mock_export.assert_called_once_with(self.state)

        # Should save game
        mock_save.assert_called_once()

        # Should stop running
        assert self.state.running is False

    @patch("soloquest.commands.session.display")
    @patch("soloquest.commands.session.Prompt.ask", return_value="")
    @patch("soloquest.commands.session._export_session")
    @patch("soloquest.commands.session.save_game", return_value="/tmp/save.json")
    def test_end_with_entries_no_title(self, mock_save, mock_export, mock_prompt, mock_display):
        """handle_end should work without title when user skips."""
        self.state.session.entries = [LogEntry(kind=EntryKind.MOVE, text="Strike")]

        handle_end(self.state, [], set())

        # Title should be empty string
        assert self.state.session.title == ""

        # Should still export
        mock_export.assert_called_once()

    @patch("soloquest.commands.session.display")
    @patch("soloquest.commands.session.save_game", return_value="/tmp/save.json")
    def test_end_with_no_entries(self, mock_save, mock_display):
        """handle_end with no entries should not export but still save."""
        # Empty session
        assert len(self.state.session.entries) == 0

        handle_end(self.state, [], set())

        # Should display message about no entries
        info_calls = [call[0][0] for call in mock_display.info.call_args_list]
        assert any("no entries" in call.lower() for call in info_calls)

        # Should save game (even with no entries)
        mock_save.assert_called_once()

        # Should stop running
        assert self.state.running is False

    @patch("soloquest.commands.session.display")
    @patch("soloquest.commands.session.Prompt.ask", return_value="")
    @patch("soloquest.commands.session._export_session")
    @patch("soloquest.commands.session.save_game", return_value="/tmp/save.json")
    def test_end_displays_session_stats_correctly(
        self, mock_save, mock_export, mock_prompt, mock_display
    ):
        """handle_end should display accurate session statistics."""
        # Create session with known stats
        self.state.session.entries = [
            LogEntry(kind=EntryKind.MOVE, text="Strike"),
            LogEntry(kind=EntryKind.MOVE, text="Face Danger"),
            LogEntry(kind=EntryKind.ORACLE, text="Action: Attack"),
            LogEntry(kind=EntryKind.JOURNAL, text="Story"),
            LogEntry(kind=EntryKind.JOURNAL, text="More story"),
            LogEntry(kind=EntryKind.NOTE, text="NPC"),
        ]

        # Add vows
        self.state.vows = [
            Vow(description="Active vow", rank=VowRank.DANGEROUS, fulfilled=False),
            Vow(description="Fulfilled vow", rank=VowRank.DANGEROUS, fulfilled=True),
        ]

        handle_end(self.state, [], set())

        # Check that stats are displayed
        info_calls = [call[0][0] for call in mock_display.info.call_args_list]
        assert any("2" in call and "Moves rolled" in call for call in info_calls)
        assert any("1" in call and "Oracles consulted" in call for call in info_calls)
        assert any("2" in call and "Journal entries" in call for call in info_calls)
        assert any("1" in call and "Notes" in call for call in info_calls)
        assert any("1" in call and "Vows fulfilled" in call for call in info_calls)
        assert any("1" in call and "Active vows" in call for call in info_calls)


class TestHandleHelp:
    """Tests for /help command."""

    def setup_method(self):
        self.state = MagicMock()
        self.state.character = Character(
            name="Kael", stats=Stats(edge=2, heart=1, iron=3, shadow=2, wits=3)
        )
        # Mock moves and oracles
        self.state.moves = {
            "strike": {"name": "Strike", "category": "combat"},
            "face_danger": {"name": "Face Danger", "category": "adventure"},
            "compel": {"name": "Compel", "category": "relationship"},
        }
        self.state.oracles = {
            "action": MagicMock(name="Action"),
            "theme": MagicMock(name="Theme"),
        }

    @patch("soloquest.commands.session.display")
    @patch("soloquest.commands.registry.COMMAND_HELP", {"move": "move — resolve a move", "oracle": "oracle — consult oracle"})
    def test_help_with_no_args_shows_command_list(self, mock_display):
        """handle_help with no args should show all commands."""
        handle_help(self.state, [], set())

        mock_display.rule.assert_called_once_with("Help")
        # Should print commands
        assert mock_display.console.print.call_count > 0

    @patch("soloquest.commands.session.display")
    def test_help_moves_shows_categorized_moves(self, mock_display):
        """handle_help moves should show categorized move list."""
        handle_help(self.state, ["moves"], set())

        mock_display.rule.assert_called_once_with("Available Moves")

        # Should print categories and move names
        print_calls = mock_display.console.print.call_args_list
        # Extract the actual printed text
        printed_text = " ".join([str(call[0][0]) if call[0] else "" for call in print_calls])
        assert "Strike" in printed_text
        assert "Face Danger" in printed_text
        assert "Compel" in printed_text

    @patch("soloquest.commands.session.display")
    def test_help_oracles_shows_oracle_list(self, mock_display):
        """handle_help oracles should show available oracles."""
        handle_help(self.state, ["oracles"], set())

        mock_display.rule.assert_called_once_with("Available Oracles")

        # Should print oracle names
        assert mock_display.console.print.call_count > 0

    @patch("soloquest.commands.session.display")
    @patch("soloquest.commands.registry.COMMAND_HELP", {"move": "move — resolve a move"})
    def test_help_specific_command_shows_details(self, mock_display):
        """handle_help with specific command should show that command's help."""
        handle_help(self.state, ["move"], set())

        mock_display.info.assert_called_once()
        call_args = mock_display.info.call_args[0][0]
        assert "move" in call_args.lower()

    @patch("soloquest.commands.session.display")
    def test_help_unknown_topic_shows_error(self, mock_display):
        """handle_help with unknown topic should show error."""
        handle_help(self.state, ["invalid_topic"], set())

        mock_display.error.assert_called_once()
        call_args = mock_display.error.call_args[0][0]
        assert "unknown" in call_args.lower() or "Unknown" in call_args
