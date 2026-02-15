"""Dice provider abstraction supporting digital, physical, and mixed modes."""

from __future__ import annotations

import random
from enum import StrEnum
from typing import Protocol

from rich.console import Console
from rich.prompt import Prompt

console = Console()


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

    def roll(self, die: Die) -> int:
        low, high = DIE_RANGES[die]
        while True:
            raw = Prompt.ask(f"  Roll your [bold]{die}[/bold] ({low}–{high})")
            try:
                value = int(raw.strip())
                if low <= value <= high:
                    return value
                console.print(f"  [yellow]⚠ Enter a number between {low} and {high}.[/yellow]")
            except ValueError:
                console.print("  [yellow]⚠ Please enter a number.[/yellow]")


class MixedDice:
    """Digital by default; can be overridden per-roll."""

    def __init__(self) -> None:
        self._digital = DigitalDice()
        self._physical = PhysicalDice()
        self._force_physical: bool = False

    def roll(self, die: Die) -> int:
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
) -> tuple[int, int, int]:
    """Roll action die (d6) and two challenge dice (d10).

    Returns:
        (action_die, challenge_1, challenge_2)
    """
    action = provider.roll(Die.D6)
    c1 = provider.roll(Die.D10)
    c2 = provider.roll(Die.D10)
    return action, c1, c2


def roll_challenge_dice(
    provider: DigitalDice | PhysicalDice | MixedDice,
) -> tuple[int, int]:
    """Roll two challenge dice (d10) — used for progress rolls."""
    c1 = provider.roll(Die.D10)
    c2 = provider.roll(Die.D10)
    return c1, c2


def roll_oracle(
    provider: DigitalDice | PhysicalDice | MixedDice,
) -> int:
    """Roll d100 for oracle lookup."""
    return provider.roll(Die.D100)
