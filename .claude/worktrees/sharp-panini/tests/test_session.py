"""Tests for the Session model."""

from __future__ import annotations

from starforged.models.session import EntryKind, LogEntry, Session


class TestLogEntry:
    def test_serialization_roundtrip(self):
        entry = LogEntry(kind=EntryKind.JOURNAL, text="I step through the airlock.")
        data = entry.to_dict()
        restored = LogEntry.from_dict(data)
        assert restored.kind == EntryKind.JOURNAL
        assert restored.text == "I step through the airlock."

    def test_mechanical_kind(self):
        entry = LogEntry(kind=EntryKind.MECHANICAL, text="Health -1 (now 4/5)")
        assert entry.kind == EntryKind.MECHANICAL


class TestSession:
    def setup_method(self):
        self.session = Session(number=3, title="The Derelict")

    def test_add_journal_entry(self):
        self.session.add_journal("  The docking clamps release.  ")
        assert len(self.session.entries) == 1
        assert self.session.entries[0].kind == EntryKind.JOURNAL
        assert self.session.entries[0].text == "The docking clamps release."

    def test_add_journal_strips_whitespace(self):
        self.session.add_journal("  leading and trailing  ")
        assert self.session.entries[0].text == "leading and trailing"

    def test_add_move_entry(self):
        self.session.add_move("**Strike** | Iron 3 | 5+3 = 8 vs [4,7] → STRONG HIT")
        assert self.session.entries[0].kind == EntryKind.MOVE

    def test_add_oracle_entry(self):
        self.session.add_oracle("Oracle [Action] roll 47 → Destroy")
        assert self.session.entries[0].kind == EntryKind.ORACLE

    def test_add_mechanical_entry(self):
        self.session.add_mechanical("Momentum +1 (now 6)")
        assert self.session.entries[0].kind == EntryKind.MECHANICAL

    def test_add_note_entry(self):
        self.session.add_note("NPC: Commander Vex — hostile")
        assert self.session.entries[0].kind == EntryKind.NOTE

    def test_multiple_entries_ordered(self):
        self.session.add_journal("First")
        self.session.add_move("Strike result")
        self.session.add_journal("Second")
        assert len(self.session.entries) == 3
        assert self.session.entries[0].text == "First"
        assert self.session.entries[1].kind == EntryKind.MOVE
        assert self.session.entries[2].text == "Second"

    def test_serialization_roundtrip(self):
        self.session.add_journal("Test entry")
        self.session.add_mechanical("Health -1")
        data = self.session.to_dict()
        restored = Session.from_dict(data)
        assert restored.number == 3
        assert restored.title == "The Derelict"
        assert len(restored.entries) == 2
        assert restored.entries[0].text == "Test entry"
