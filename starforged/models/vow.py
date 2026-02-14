"""Vow model with progress track."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VowRank(StrEnum):
    TROUBLESOME = "troublesome"
    DANGEROUS = "dangerous"
    FORMIDABLE = "formidable"
    EXTREME = "extreme"
    EPIC = "epic"


# Ticks added per progress mark (out of 40 total ticks = 10 boxes of 4)
PROGRESS_TICKS: dict[VowRank, int] = {
    VowRank.TROUBLESOME: 12,  # 3 boxes
    VowRank.DANGEROUS: 8,  # 2 boxes
    VowRank.FORMIDABLE: 4,  # 1 box
    VowRank.EXTREME: 2,  # 2 ticks
    VowRank.EPIC: 1,  # 1 tick
}

MAX_TICKS = 40  # 10 boxes × 4 ticks


@dataclass
class Vow:
    description: str
    rank: VowRank
    ticks: int = 0
    fulfilled: bool = False

    @property
    def progress_score(self) -> int:
        """Progress score for fulfillment roll (ticks // 4, max 10)."""
        return min(self.ticks // 4, 10)

    @property
    def boxes_filled(self) -> int:
        return self.ticks // 4

    @property
    def partial_ticks(self) -> int:
        return self.ticks % 4

    def mark_progress(self) -> int:
        """Add progress ticks for this vow's rank. Returns new tick count."""
        tick_gain = PROGRESS_TICKS[self.rank]
        self.ticks = min(MAX_TICKS, self.ticks + tick_gain)
        return self.ticks

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "rank": self.rank.value,
            "ticks": self.ticks,
            "fulfilled": self.fulfilled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Vow:
        return cls(
            description=data["description"],
            rank=VowRank(data["rank"]),
            ticks=data.get("ticks", 0),
            fulfilled=data.get("fulfilled", False),
        )


def fuzzy_match_vow(query: str, vows: list[Vow]) -> list[Vow]:
    q = query.lower()
    return [v for v in vows if q in v.description.lower()]


# Spirit cost when forsaking a vow, by rank
SPIRIT_COST: dict[VowRank, int] = {
    VowRank.TROUBLESOME: 1,
    VowRank.DANGEROUS: 2,
    VowRank.FORMIDABLE: 3,
    VowRank.EXTREME: 4,
    VowRank.EPIC: 5,
}
