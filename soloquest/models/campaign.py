"""Campaign model — shared state for co-op campaigns."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class PlayerInfo:
    joined: str  # ISO 8601 datetime string

    def to_dict(self) -> dict[str, Any]:
        return {"joined": self.joined}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> PlayerInfo:
        return cls(joined=d["joined"])


@dataclass
class CampaignState:
    """Shared campaign metadata stored in campaign.toml."""

    name: str
    slug: str
    created: str  # ISO 8601 datetime string
    players: dict[str, PlayerInfo] = field(default_factory=dict)

    @property
    def campaign_dir(self) -> Path | None:
        """Not stored in TOML — injected after load by state layer."""
        return getattr(self, "_campaign_dir", None)

    def set_campaign_dir(self, path: Path) -> None:
        self._campaign_dir = path

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign": {
                "name": self.name,
                "slug": self.slug,
                "created": self.created,
            },
            "players": {pid: info.to_dict() for pid, info in self.players.items()},
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CampaignState:
        camp = d.get("campaign", d)
        players = {pid: PlayerInfo.from_dict(info) for pid, info in d.get("players", {}).items()}
        return cls(
            name=camp["name"],
            slug=camp["slug"],
            created=camp["created"],
            players=players,
        )

    @classmethod
    def create(cls, name: str) -> CampaignState:
        """Create a new CampaignState with a generated slug and timestamp."""
        slug = name.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        now = datetime.now(UTC).isoformat()
        return cls(name=name, slug=slug, created=now)
