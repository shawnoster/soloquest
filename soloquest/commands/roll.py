"""Raw dice roll command — /roll [dice expression]."""

from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

from soloquest.engine.dice import Die
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState

# e.g. "2d10", "d6", "1d100", "3d6"
DICE_PATTERN = re.compile(r"^(\d*)d(\d+)$", re.IGNORECASE)

# Known named dice for physical prompting
NAMED_DICE = {
    6: Die.D6,
    10: Die.D10,
    100: Die.D100,
}


def handle_roll(state: GameState, args: list[str], flags: set[str]) -> None:
    """/roll [dice] [note] — e.g. /roll d6  /roll 2d10  /roll d100 inciting incident"""
    if not args:
        display.error("Usage: /roll [dice]  (e.g. /roll d6, /roll 2d10, /roll d100)")
        return

    expr = args[0].lower().strip()
    note = " ".join(args[1:]) if len(args) > 1 else ""

    m = DICE_PATTERN.match(expr)
    if not m:
        display.error(f"Can't parse dice expression '{expr}'. Try: d6, 2d10, d100")
        return

    count = int(m.group(1)) if m.group(1) else 1
    sides = int(m.group(2))

    if count < 1 or count > 20:
        display.error("Roll between 1 and 20 dice at once.")
        return
    if sides < 2:
        display.error("Dice must have at least 2 sides.")
        return

    # Use the game's dice provider if it's a known die type; else digital fallback
    named = NAMED_DICE.get(sides)
    rolls: list[int] = []

    for _ in range(count):
        if named:
            rolls.append(state.dice.roll(named))
        else:
            # Arbitrary die — always digital
            rolls.append(random.randint(1, sides))

    total = sum(rolls)
    rolls_str = " + ".join(str(r) for r in rolls) if count > 1 else str(rolls[0])
    result_str = f"{rolls_str} = [bold]{total}[/bold]" if count > 1 else f"[bold]{rolls[0]}[/bold]"

    if note:
        display.console.print(f"  [blue]│[/blue]  [dim italic]{note}[/dim italic]")
    display.console.print(f"  [blue]└[/blue]  🎲 [dim]{count}d{sides}[/dim]  {result_str}")

    log_text = f"Roll {count}d{sides}: {rolls_str}" + (f" = {total}" if count > 1 else "")
    if note:
        log_text += f" — {note}"
    state.session.add_mechanical(log_text)
