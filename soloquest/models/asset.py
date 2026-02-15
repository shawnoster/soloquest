"""Asset models for Ironsworn: Starforged."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssetAbility:
    """A single ability within an asset."""

    text: str
    enabled: bool = False


@dataclass
class AssetTrack:
    """A condition meter or track on an asset (e.g., integrity, health)."""

    name: str
    min_value: int
    max_value: int
    current: int


@dataclass
class Asset:
    """Definition of an asset card."""

    key: str
    name: str
    category: str  # "path", "companion", "module", etc.
    description: str = ""
    abilities: list[AssetAbility] = field(default_factory=list)
    tracks: dict[str, tuple[int, int]] = field(default_factory=dict)  # name -> (min, max)
    inputs: list[str] = field(default_factory=list)  # custom input field names
    shared: bool = False


@dataclass
class CharacterAsset:
    """Instance of an asset owned by a character.

    Stores the state of abilities (unlocked/enabled) and track values.
    """

    asset_key: str  # Reference to Asset definition
    abilities_unlocked: list[bool] = field(default_factory=list)  # [True, False, False]
    track_values: dict[str, int] = field(default_factory=dict)  # {"health": 2}
    input_values: dict[str, str] = field(default_factory=dict)  # {"name": "Rusty"}
