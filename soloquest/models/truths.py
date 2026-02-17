"""Truth models for campaign setting creation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TruthOption:
    """A single option for a truth category."""

    roll_range: tuple[int, int]
    summary: str
    text: str
    quest_starter: str = ""
    subchoices: list[str] = field(default_factory=list)

    def matches_roll(self, roll: int) -> bool:
        """Check if a roll value matches this option's range."""
        return self.roll_range[0] <= roll <= self.roll_range[1]


@dataclass
class TruthCategory:
    """A truth category with multiple options."""

    name: str
    description: str
    order: int
    options: list[TruthOption] = field(default_factory=list)

    def get_option_by_roll(self, roll: int) -> TruthOption | None:
        """Get the option that matches a given roll."""
        for option in self.options:
            if option.matches_roll(roll):
                return option
        return None


@dataclass
class ChosenTruth:
    """A player's chosen truth for their campaign."""

    category: str
    option_summary: str
    option_text: str = ""
    custom_text: str = ""
    quest_starter: str = ""
    subchoice: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "category": self.category,
            "option_summary": self.option_summary,
            "option_text": self.option_text,
            "custom_text": self.custom_text,
            "quest_starter": self.quest_starter,
            "subchoice": self.subchoice,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ChosenTruth:
        """Deserialize from dictionary."""
        return cls(
            category=data["category"],
            option_summary=data["option_summary"],
            option_text=data.get("option_text", ""),
            custom_text=data.get("custom_text", ""),
            quest_starter=data.get("quest_starter", ""),
            subchoice=data.get("subchoice", ""),
        )

    def display_text(self) -> str:
        """Get the display text (custom if present, otherwise option summary)."""
        text = self.custom_text or self.option_summary
        if self.subchoice:
            text += f" ({self.subchoice})"
        return text
