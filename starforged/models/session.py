"""Session log model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class EntryKind(StrEnum):
    JOURNAL = "journal"
    MOVE = "move"
    ORACLE = "oracle"
    MECHANICAL = "mechanical"  # track adjustments, momentum, etc.
    NOTE = "note"


@dataclass
class LogEntry:
    kind: EntryKind
    text: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> LogEntry:
        return cls(
            kind=EntryKind(data["kind"]),
            text=data["text"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class Session:
    number: int
    title: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    entries: list[LogEntry] = field(default_factory=list)

    def add_journal(self, text: str) -> None:
        self.entries.append(LogEntry(kind=EntryKind.JOURNAL, text=text.strip()))

    def add_move(self, text: str) -> None:
        self.entries.append(LogEntry(kind=EntryKind.MOVE, text=text.strip()))

    def add_oracle(self, text: str) -> None:
        self.entries.append(LogEntry(kind=EntryKind.ORACLE, text=text.strip()))

    def add_mechanical(self, text: str) -> None:
        self.entries.append(LogEntry(kind=EntryKind.MECHANICAL, text=text.strip()))

    def add_note(self, text: str) -> None:
        self.entries.append(LogEntry(kind=EntryKind.NOTE, text=text.strip()))

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "title": self.title,
            "started_at": self.started_at.isoformat(),
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        entries = [LogEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            number=data["number"],
            title=data.get("title", ""),
            started_at=datetime.fromisoformat(data["started_at"]),
            entries=entries,
        )
