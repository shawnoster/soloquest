"""Dice provider abstraction supporting digital, physical, and mixed modes."""

from __future__ import annotations

import random
from enum import StrEnum
from typing import Protocol

from rich.prompt import Prompt

from soloquest.ui.console import console


class DiceMode(StrEnum):
    DIGITAL = "digital"
    PHYSICAL = "physical"
    MIXED = "mixed"


class Die(StrEnum):
    D6 = "d6"
    D10 = "d10"
    D100 = "d100"


DIE_RANGES: dict[Die, tuple[int, int]] = {
    Die.D6: (1, 6),
    Die.D10: (1, 10),
    Die.D100: (1, 100),
}


class DiceProvider(Protocol):
    def roll(self, die: Die) -> int: ...


class DigitalDice:
    """Rolls dice using Python's random module."""

    def roll(self, die: Die) -> int:
        low, high = DIE_RANGES[die]
        return random.randint(low, high)


class PhysicalDice:
    """Prompts the player for each die result."""

    def roll(self, die: Die) -> int | None:
        """Prompt for a die roll. Returns None if cancelled (Ctrl+C or typing 'cancel')."""
        low, high = DIE_RANGES[die]
        while True:
            try:
                raw = Prompt.ask(f"  Roll your [bold]{die}[/bold] ({low}–{high}) or 'cancel'")
                raw_lower = raw.strip().lower()
                if raw_lower in ["cancel", "back", "quit", "exit"]:
                    return None
                try:
                    value = int(raw.strip())
                    if low <= value <= high:
                        return value
                    console.print(f"  [yellow]⚠ Enter a number between {low} and {high}.[/yellow]")
                except ValueError:
                    console.print("  [yellow]⚠ Please enter a number.[/yellow]")
            except (KeyboardInterrupt, EOFError):
                console.print()
                return None


class MixedDice:
    """Digital by default; can be overridden per-roll."""

    def __init__(self) -> None:
        self._digital = DigitalDice()
        self._physical = PhysicalDice()
        self._force_physical: bool = False

    def roll(self, die: Die) -> int | None:
        """Roll a die. Returns None if cancelled (physical mode only)."""
        if self._force_physical:
            return self._physical.roll(die)
        return self._digital.roll(die)

    def set_manual(self, enabled: bool) -> None:
        """Force physical prompts for the next roll sequence."""
        self._force_physical = enabled


def make_dice_provider(mode: DiceMode) -> DigitalDice | PhysicalDice | MixedDice:
    match mode:
        case DiceMode.DIGITAL:
            return DigitalDice()
        case DiceMode.PHYSICAL:
            return PhysicalDice()
        case DiceMode.MIXED:
            return MixedDice()


def roll_action_dice(
    provider: DigitalDice | PhysicalDice | MixedDice,
) -> tuple[int, int, int] | None:
    """Roll action die (d6) and two challenge dice (d10).

    Returns:
        (action_die, challenge_1, challenge_2) or None if cancelled
    """
    action = provider.roll(Die.D6)
    if action is None:
        return None
    c1 = provider.roll(Die.D10)
    if c1 is None:
        return None
    c2 = provider.roll(Die.D10)
    if c2 is None:
        return None
    return action, c1, c2


def roll_challenge_dice(
    provider: DigitalDice | PhysicalDice | MixedDice,
) -> tuple[int, int] | None:
    """Roll two challenge dice (d10) — used for progress rolls. Returns None if cancelled."""
    c1 = provider.roll(Die.D10)
    if c1 is None:
        return None
    c2 = provider.roll(Die.D10)
    if c2 is None:
        return None
    return c1, c2


def roll_oracle(
    provider: DigitalDice | PhysicalDice | MixedDice,
) -> int | None:
    """Roll d100 for oracle lookup. Returns None if cancelled."""
    return provider.roll(Die.D100)
