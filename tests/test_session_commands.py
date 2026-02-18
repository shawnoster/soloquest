"""Tests for session command handlers."""

from unittest.mock import MagicMock, patch

from soloquest.commands.session import handle_log, handle_note
from soloquest.models.character import Character, Stats
from soloquest.models.session import EntryKind, LogEntry, Session


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
