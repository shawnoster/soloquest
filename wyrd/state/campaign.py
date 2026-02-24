"""Campaign directory management — create, join, load, save campaigns."""

from __future__ import annotations

import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from wyrd.config import config
from wyrd.models.campaign import CampaignState, PlayerInfo

if TYPE_CHECKING:
    pass

try:
    import tomli_w as _tomli_w

    def _dump_toml(data: dict) -> str:  # type: ignore[misc]
        return _tomli_w.dumps(data)

except ImportError:
    # tomli_w not available — fall back to manual TOML writing
    def _dump_toml(data: dict) -> str:  # type: ignore[misc]
        return _dict_to_toml(data)


def _dict_to_toml(data: dict, prefix: str = "") -> str:  # type: ignore[misc]
    """Minimal TOML serializer for campaign.toml (no nested arrays needed)."""
    lines: list[str] = []
    scalars: dict = {}
    tables: dict = {}

    for key, value in data.items():
        if isinstance(value, dict):
            tables[key] = value
        else:
            scalars[key] = value

    for key, value in scalars.items():
        if isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, bool):
            lines.append(f"{key} = {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key} = {value}")

    for key, value in tables.items():
        section = f"{prefix}.{key}" if prefix else key
        lines.append(f"\n[{section}]")
        for k, v in value.items():
            if isinstance(v, str):
                lines.append(f'{k} = "{v}"')
            elif isinstance(v, dict):
                # Nested table — e.g. players.kira
                lines.append(f"\n[{section}.{k}]")
                for kk, vv in v.items():
                    if isinstance(vv, str):
                        lines.append(f'{kk} = "{vv}"')

    return "\n".join(lines) + "\n"


def campaigns_dir() -> Path:
    """Return the campaigns base directory."""
    return config.adventures_dir / "campaigns"


def campaign_path(slug: str) -> Path:
    """Return the directory for a named campaign."""
    return campaigns_dir() / slug


def list_campaigns() -> list[str]:
    """Return slugs of all existing campaigns."""
    base = campaigns_dir()
    if not base.exists():
        return []
    return [p.name for p in sorted(base.iterdir()) if p.is_dir()]


def load_campaign(campaign_dir: Path) -> CampaignState:
    """Load campaign.toml from a campaign directory."""
    toml_path = campaign_dir / "campaign.toml"
    with toml_path.open("rb") as f:
        data = tomllib.load(f)
    campaign = CampaignState.from_dict(data)
    campaign.set_campaign_dir(campaign_dir)
    return campaign


def save_campaign(campaign: CampaignState, campaign_dir: Path) -> None:
    """Write campaign.toml."""
    campaign_dir.mkdir(parents=True, exist_ok=True)
    toml_path = campaign_dir / "campaign.toml"
    toml_path.write_text(_dict_to_toml(campaign.to_dict()), encoding="utf-8")


def create_campaign(name: str, player_id: str) -> tuple[CampaignState, Path]:
    """Create a new campaign directory with the given player as first member.

    Returns (campaign, campaign_dir).
    """
    campaign = CampaignState.create(name)
    campaign_dir = campaign_path(campaign.slug)

    if campaign_dir.exists():
        raise ValueError(f"Campaign '{campaign.slug}' already exists at {campaign_dir}")

    campaign_dir.mkdir(parents=True, exist_ok=True)
    (campaign_dir / "events").mkdir()
    (campaign_dir / "players").mkdir()

    campaign.players[player_id] = PlayerInfo(joined=datetime.now(UTC).isoformat())
    campaign.set_campaign_dir(campaign_dir)
    save_campaign(campaign, campaign_dir)
    return campaign, campaign_dir


def join_campaign(campaign_dir: Path, player_id: str) -> CampaignState:
    """Add a player to an existing campaign.

    Returns the updated CampaignState.
    Idempotent: if player is already a member, returns the campaign as-is.
    """
    campaign = load_campaign(campaign_dir)
    if player_id in campaign.players:
        return campaign
    campaign.players[player_id] = PlayerInfo(joined=datetime.now(UTC).isoformat())
    save_campaign(campaign, campaign_dir)
    return campaign


def player_save_path(campaign_dir: Path, player_id: str) -> Path:
    """Return the character save path for a player within a campaign."""
    slug = player_id.lower().replace(" ", "_")
    return campaign_dir / "players" / f"{slug}.json"
