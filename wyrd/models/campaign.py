"""Campaign model — shared state for co-op campaigns."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from wyrd.models.truths import ChosenTruth
    from wyrd.models.vow import Vow


@dataclass
class TruthProposal:
    """A pending truth proposal awaiting partner approval."""

    category: str
    option_summary: str
    proposer: str
    proposed_at: str  # ISO 8601
    custom_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "category": self.category,
            "option_summary": self.option_summary,
            "proposer": self.proposer,
            "proposed_at": self.proposed_at,
        }
        if self.custom_text:
            d["custom_text"] = self.custom_text
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> TruthProposal:
        return cls(
            category=d["category"],
            option_summary=d["option_summary"],
            proposer=d["proposer"],
            proposed_at=d["proposed_at"],
            custom_text=d.get("custom_text", ""),
        )


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
    truths: list[ChosenTruth] = field(default_factory=list)  # type: ignore[type-arg]
    pending_truth_proposals: dict[str, TruthProposal] = field(default_factory=dict)

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
        if self.truths:
            d["truths"] = [t.to_dict() for t in self.truths]
        if self.pending_truth_proposals:
            d["pending_truth_proposals"] = {
                cat: p.to_dict() for cat, p in self.pending_truth_proposals.items()
            }
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CampaignState:
        from wyrd.models.truths import ChosenTruth
        from wyrd.models.vow import Vow

        camp = d.get("campaign", d)
        players = {pid: PlayerInfo.from_dict(info) for pid, info in d.get("players", {}).items()}
        shared_vows = [Vow.from_dict(v) for v in d.get("shared_vows", [])]
        truths = [ChosenTruth.from_dict(t) for t in d.get("truths", [])]
        pending_truth_proposals = {
            cat: TruthProposal.from_dict(p)
            for cat, p in d.get("pending_truth_proposals", {}).items()
        }
        return cls(
            name=camp["name"],
            slug=camp["slug"],
            created=camp["created"],
            players=players,
            shared_vows=shared_vows,
            truths=truths,
            pending_truth_proposals=pending_truth_proposals,
        )

    @classmethod
    def create(cls, name: str) -> CampaignState:
        """Create a new CampaignState with a generated slug and timestamp."""
        slug = name.lower().replace(" ", "-")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        now = datetime.now(UTC).isoformat()
        return cls(name=name, slug=slug, created=now)
