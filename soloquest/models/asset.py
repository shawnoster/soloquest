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

    Stores the state of abilities (unlocked/enabled), track values, and conditions.
    """

    asset_key: str  # Reference to Asset definition
    abilities_unlocked: list[bool] = field(default_factory=list)  # [True, False, False]
    track_values: dict[str, int] = field(default_factory=dict)  # {"health": 2}
    input_values: dict[str, str] = field(default_factory=dict)  # {"name": "Rusty"}
    conditions: set[str] = field(default_factory=set)  # {"battered"}

    def to_dict(self) -> dict:
        return {
            "asset_key": self.asset_key,
            "abilities_unlocked": self.abilities_unlocked,
            "track_values": self.track_values,
            "input_values": self.input_values,
            "conditions": sorted(self.conditions),
        }

    @classmethod
    def from_dict(cls, data: dict | str) -> CharacterAsset:
        if isinstance(data, str):
            return cls(asset_key=data)
        return cls(
            asset_key=data["asset_key"],
            abilities_unlocked=data.get("abilities_unlocked", []),
            track_values=data.get("track_values", {}),
            input_values=data.get("input_values", {}),
            conditions=set(data.get("conditions", [])),
        )

    def adjust_track(self, name: str, delta: int, min_val: int, max_val: int) -> int:
        """Adjust meter by delta, clamped to [min_val, max_val]. Returns new value."""
        current = self.track_values.get(name, max_val)
        new_val = max(min_val, min(max_val, current + delta))
        self.track_values[name] = new_val
        return new_val

    def toggle_condition(self, name: str) -> bool:
        """Toggle a condition. Returns True if now active."""
        name_lower = name.lower()
        if name_lower in self.conditions:
            self.conditions.discard(name_lower)
            return False
        self.conditions.add(name_lower)
        return True
