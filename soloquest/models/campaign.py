"""Campaign model — shared state for co-op campaigns."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from soloquest.models.vow import Vow


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
    shared_vows: list[Vow] = field(default_factory=list)  # type: ignore[type-arg]

    @property
    def campaign_dir(self) -> Path | None:
        """Not stored in TOML — injected after load by state layer."""
        return getattr(self, "_campaign_dir", None)

    def set_campaign_dir(self, path: Path) -> None:
        self._campaign_dir = path

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "campaign": {
                "name": self.name,
                "slug": self.slug,
                "created": self.created,
            },
            "players": {pid: info.to_dict() for pid, info in self.players.items()},
        }
        if self.shared_vows:
            d["shared_vows"] = [v.to_dict() for v in self.shared_vows]
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CampaignState:
        from soloquest.models.vow import Vow

        camp = d.get("campaign", d)
        players = {pid: PlayerInfo.from_dict(info) for pid, info in d.get("players", {}).items()}
        shared_vows = [Vow.from_dict(v) for v in d.get("shared_vows", [])]
        return cls(
            name=camp["name"],
            slug=camp["slug"],
            created=camp["created"],
            players=players,
            shared_vows=shared_vows,
        )

    @classmethod
    def create(cls, name: str) -> CampaignState:
        """Create a new CampaignState with a generated slug and timestamp."""
        slug = name.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        now = datetime.now(UTC).isoformat()
        return cls(name=name, slug=slug, created=now)
