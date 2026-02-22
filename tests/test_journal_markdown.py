"""Tests for markdown support in journal entries."""

from unittest.mock import patch

from soloquest.models.session import EntryKind, LogEntry
from soloquest.ui.display import log_entry


class TestJournalMarkdown:
    """Test markdown rendering in journal entries."""

    def test_italic_text_is_rendered(self):
        """Journal entries with *italic* should render with emphasis."""
        entry = LogEntry(kind=EntryKind.JOURNAL, text="This is *italic* text")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(entry)

            # Should have called console.print at least once for the Markdown object
            assert mock_console.print.called

    def test_bold_text_is_rendered(self):
        """Journal entries with **bold** should render with strong emphasis."""
        entry = LogEntry(kind=EntryKind.JOURNAL, text="This is **bold** text")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(entry)

            assert mock_console.print.called

    def test_mixed_formatting_is_rendered(self):
        """Journal entries can combine *italic* and **bold** formatting."""
        entry = LogEntry(kind=EntryKind.JOURNAL, text="This has *italic* and **bold** together")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(entry)

            assert mock_console.print.called

    def test_quote_block_is_rendered(self):
        """Journal entries with > quote syntax should render as quote blocks."""
        entry = LogEntry(kind=EntryKind.JOURNAL, text="> This is a quote block")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(entry)

            assert mock_console.print.called

    def test_plain_text_without_markdown_works(self):
        """Journal entries without markdown should render normally."""
        entry = LogEntry(kind=EntryKind.JOURNAL, text="This is plain text")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(entry)

            assert mock_console.print.called

    def test_journal_with_label_shows_label(self):
        """Journal entries with show_label=True should display the label."""
        entry = LogEntry(kind=EntryKind.JOURNAL, text="Test entry")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(entry, show_label=True)

            # Should print label separately, then the Markdown content
            assert mock_console.print.call_count >= 2

    def test_raw_markdown_preserved_in_model(self):
        """LogEntry should store raw markdown, not processed HTML/markup."""
        text_with_markdown = "The ship's AI says: *\"Welcome aboard.\"*"
        entry = LogEntry(kind=EntryKind.JOURNAL, text=text_with_markdown)

        # Raw text should be preserved
        assert entry.text == text_with_markdown

        # Serialization should preserve it
        data = entry.to_dict()
        assert data["text"] == text_with_markdown

        # Deserialization should preserve it
        restored = LogEntry.from_dict(data)
        assert restored.text == text_with_markdown

    def test_non_journal_entries_unaffected(self):
        """Non-JOURNAL entries should not use markdown rendering."""
        move_entry = LogEntry(kind=EntryKind.MOVE, text="Strike **Iron** 3")
        oracle_entry = LogEntry(kind=EntryKind.ORACLE, text="Action: *Attack*")
        note_entry = LogEntry(kind=EntryKind.NOTE, text="NPC: **Commander** Vex")

        with patch("soloquest.ui.display.console") as mock_console:
            log_entry(move_entry)
            log_entry(oracle_entry)
            log_entry(note_entry)

            # All should still render (though not as markdown)
            assert mock_console.print.call_count == 3
