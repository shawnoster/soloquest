"""Character model."""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Debilities ─────────────────────────────────────────────────────────────────
# Conditions that reduce momentum_max and/or momentum_reset
# Each active debility reduces momentum_max by 1.
# Two or more active debilities also reduce momentum_reset to 0.

DEBILITY_NAMES = [
    "wounded",
    "shaken",
    "unprepared",
    "encumbered",
    "maimed",
    "corrupted",
]

MOMENTUM_MAX_BASE = 10
MOMENTUM_RESET_BASE = 2


@dataclass
class Stats:
    edge: int = 1
    heart: int = 1
    iron: int = 1
    shadow: int = 1
    wits: int = 1

    def get(self, name: str) -> int:
        """Get a stat by name. Raises ValueError if stat name is invalid."""
        name_lower = name.lower()
        if name_lower not in ("edge", "heart", "iron", "shadow", "wits"):
            raise ValueError(f"Invalid stat name: {name}")
        return getattr(self, name_lower)

    def as_dict(self) -> dict[str, int]:
        return {
            "edge": self.edge,
            "heart": self.heart,
            "iron": self.iron,
            "shadow": self.shadow,
            "wits": self.wits,
        }


@dataclass
class Character:
    name: str
    homeworld: str = ""
    stats: Stats = field(default_factory=Stats)

    # Tracks (0–5)
    health: int = 5
    spirit: int = 5
    supply: int = 3

    # Momentum (-6 to +10, modified by debilities)
    momentum: int = 2

    # Debilities — stored as set of active debility names
    debilities: set[str] = field(default_factory=set)

    # Assets (keys into asset registry)
    assets: list[str] = field(default_factory=list)

    # ── Computed momentum bounds ────────────────────────────────────────────
    @property
    def momentum_max(self) -> int:
        """Max momentum decreases by 1 per active debility."""
        return max(0, MOMENTUM_MAX_BASE - len(self.debilities))

    @property
    def momentum_reset(self) -> int:
        """Reset value drops to 0 if 2+ debilities are active."""
        return 0 if len(self.debilities) >= 2 else MOMENTUM_RESET_BASE

    def adjust_track(self, track: str, delta: int) -> int:
        """Adjust a track (health/spirit/supply) by delta, clamped 0–5. Returns new value."""
        current = getattr(self, track)
        new_val = max(0, min(5, current + delta))
        setattr(self, track, new_val)
        return new_val

    def adjust_momentum(self, delta: int) -> int:
        """Adjust momentum, clamped -6 to momentum_max. Returns new value."""
        self.momentum = max(-6, min(self.momentum_max, self.momentum + delta))
        return self.momentum

    def burn_momentum(self) -> int:
        """Burn momentum, reset to momentum_reset. Returns value before burn."""
        old = self.momentum
        self.momentum = self.momentum_reset
        return old

    def toggle_debility(self, name: str) -> bool | None:
        """Toggle a debility on/off. Returns True if now active, False if removed, None if invalid."""
        name = name.lower()
        if name not in DEBILITY_NAMES:
            # Return None instead of raising to allow graceful handling
            return None
        if name in self.debilities:
            self.debilities.discard(name)
            # Re-clamp momentum to new max
            self.momentum = min(self.momentum, self.momentum_max)
            return False
        else:
            self.debilities.add(name)
            self.momentum = min(self.momentum, self.momentum_max)
            return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "homeworld": self.homeworld,
            "stats": self.stats.as_dict(),
            "health": self.health,
            "spirit": self.spirit,
            "supply": self.supply,
            "momentum": self.momentum,
            "debilities": sorted(self.debilities),
            "assets": self.assets,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Character:
        stats = Stats(**data.get("stats", {}))
        return cls(
            name=data["name"],
            homeworld=data.get("homeworld", ""),
            stats=stats,
            health=data.get("health", 5),
            spirit=data.get("spirit", 5),
            supply=data.get("supply", 3),
            momentum=data.get("momentum", 2),
            debilities=set(data.get("debilities", [])),
            assets=data.get("assets", []),
        )
