"""Tests for recent_log display function."""

from unittest.mock import patch

from soloquest.models.session import EntryKind, LogEntry
from soloquest.ui.display import recent_log


class TestRecentLog:
    """Tests for recent_log function."""

    def test_recent_log_includes_move_entries(self):
        """recent_log should include MOVE entries when displaying recent context."""
        entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="I enter the chamber."),
            LogEntry(kind=EntryKind.MOVE, text="**Strike** | d6(5)+iron(3) = 8 vs [4, 7] → STRONG HIT"),
            LogEntry(kind=EntryKind.JOURNAL, text="The enemy falls."),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            recent_log(entries, n=5)

        # Should call console.print multiple times (rule, entries, empty line)
        assert mock_console.print.call_count >= 3

        # Check that move entry was included
        printed_outputs = [str(call[0][0]) if call[0] else "" for call in mock_console.print.call_args_list]
        move_printed = any("Strike" in output and "STRONG HIT" in output for output in printed_outputs)
        assert move_printed, "Move entry should be included in recent log"

    def test_recent_log_includes_oracle_entries(self):
        """recent_log should include ORACLE entries."""
        entries = [
            LogEntry(kind=EntryKind.ORACLE, text="Oracle [Action] roll 42 → Advance"),
            LogEntry(kind=EntryKind.JOURNAL, text="We advance cautiously."),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            recent_log(entries, n=5)

        printed_outputs = [str(call[0][0]) if call[0] else "" for call in mock_console.print.call_args_list]
        oracle_printed = any("Oracle" in output and "Advance" in output for output in printed_outputs)
        assert oracle_printed, "Oracle entry should be included in recent log"

    def test_recent_log_includes_note_entries(self):
        """recent_log should include NOTE entries."""
        entries = [
            LogEntry(kind=EntryKind.NOTE, text="NPC: Commander Vex — hostile"),
            LogEntry(kind=EntryKind.JOURNAL, text="I prepare for battle."),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            recent_log(entries, n=5)

        printed_outputs = [str(call[0][0]) if call[0] else "" for call in mock_console.print.call_args_list]
        note_printed = any("Commander Vex" in output for output in printed_outputs)
        assert note_printed, "Note entry should be included in recent log"

    def test_recent_log_excludes_mechanical_entries(self):
        """recent_log should NOT include MECHANICAL entries."""
        entries = [
            LogEntry(kind=EntryKind.MECHANICAL, text="Health -1 (now 4/5)"),
            LogEntry(kind=EntryKind.JOURNAL, text="I continue exploring."),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            recent_log(entries, n=5)

        printed_outputs = [str(call[0][0]) if call[0] else "" for call in mock_console.print.call_args_list]
        mechanical_printed = any("Health -1" in output for output in printed_outputs)
        assert not mechanical_printed, "Mechanical entries should NOT be included in recent log"

    def test_recent_log_limits_to_n_entries(self):
        """recent_log should limit output to last n entries."""
        entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="Entry 1"),
            LogEntry(kind=EntryKind.JOURNAL, text="Entry 2"),
            LogEntry(kind=EntryKind.JOURNAL, text="Entry 3"),
            LogEntry(kind=EntryKind.MOVE, text="Entry 4 Move"),
            LogEntry(kind=EntryKind.ORACLE, text="Entry 5 Oracle"),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            recent_log(entries, n=2)

        # Get all calls to console.print
        call_count = mock_console.print.call_count
        
        # Should have printed: rule, entry 4, entry 5, empty line = at least 4 calls
        assert call_count >= 4
        
        # Check the printed content more carefully
        printed_calls = [call for call in mock_console.print.call_args_list]
        all_str_outputs = []
        for call in printed_calls:
            if call[0]:  # if there are args
                arg = call[0][0]
                # Convert to string
                all_str_outputs.append(str(arg))
        
        combined = " ".join(all_str_outputs)
        
        # Should show last 2 entries
        assert "Entry 4" in combined or "Move" in combined, "Should show entry 4"
        assert "Entry 5" in combined or "Oracle" in combined, "Should show entry 5"
        assert "Entry 1" not in combined, "Should not show entry 1"

    def test_recent_log_empty_entries(self):
        """recent_log should handle empty entries list gracefully."""
        with patch("soloquest.ui.display.console") as mock_console:
            recent_log([], n=5)

        # Should not print anything for empty list
        assert mock_console.print.call_count == 0

    def test_recent_log_all_entry_types_together(self):
        """recent_log should handle mixed entry types correctly."""
        entries = [
            LogEntry(kind=EntryKind.JOURNAL, text="We arrive at the ruins."),
            LogEntry(kind=EntryKind.MOVE, text="**Face Danger** | d6(3)+wits(3) = 6 vs [5, 8] → WEAK HIT"),
            LogEntry(kind=EntryKind.MECHANICAL, text="Momentum +1 (now 3)"),
            LogEntry(kind=EntryKind.ORACLE, text="Oracle [Action] roll 56 → Explore"),
            LogEntry(kind=EntryKind.NOTE, text="Area: Ancient Temple"),
            LogEntry(kind=EntryKind.JOURNAL, text="I discover a hidden passage."),
        ]

        with patch("soloquest.ui.display.console") as mock_console:
            recent_log(entries, n=10)

        # Collect all printed content
        all_calls = [str(call[0][0]) if call[0] else "" for call in mock_console.print.call_args_list]
        all_output = " ".join(all_calls)
        
        # Should include move
        assert "Face Danger" in all_output or "WEAK HIT" in all_output, "Should include move entry"
        
        # Should include oracle
        assert "Oracle" in all_output and "Explore" in all_output, "Should include oracle entry"
        
        # Should include note
        assert "Ancient Temple" in all_output or "📌" in all_output, "Should include note entry"
        
        # Should NOT include mechanical
        assert "Momentum +1" not in all_output, "Should NOT include mechanical entry"
