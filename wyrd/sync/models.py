"""Data models for the sync layer — Event, Proposal, Resolution."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class Resolution(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"


@dataclass
class Event:
    """A single immutable action in the campaign event log."""

    player: str
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "player": self.player,
            "type": self.type,
            "ts": self.ts.isoformat(),
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Event:
        return cls(
            id=d["id"],
            player=d["player"],
            type=d["type"],
            ts=datetime.fromisoformat(d["ts"]),
            data=d.get("data", {}),
        )


@dataclass
class Proposal:
    """A consensus request — e.g. propose_truth, interpret oracle."""

    player: str
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts: datetime = field(default_factory=lambda: datetime.now(UTC))
