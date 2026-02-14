"""Debility command handler — toggle conditions on/off."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starforged.models.character import DEBILITY_NAMES
from starforged.ui import display

if TYPE_CHECKING:
    from starforged.loop import GameState


def handle_debility(state: GameState, args: list[str], flags: set[str]) -> None:
    """/debility [name] — toggle a debility on or off."""
    if not args:
        _show_debilities(state)
        display.info("  Usage: /debility [name]")
        display.info(f"  Names: {', '.join(DEBILITY_NAMES)}")
        return

    query = args[0].lower()

    # Partial match
    matches = [d for d in DEBILITY_NAMES if d.startswith(query)]
    if not matches:
        display.error(f"Unknown debility '{query}'.")
        display.info(f"  Valid: {', '.join(DEBILITY_NAMES)}")
        return
    if len(matches) > 1:
        display.warn(f"Ambiguous: {', '.join(matches)}. Be more specific.")
        return

    debility = matches[0]
    now_active = state.character.toggle_debility(debility)

    if now_active:
        display.warn(f"Debility added: {debility.capitalize()}")
    else:
        display.success(f"Debility cleared: {debility.capitalize()}")

    display.debility_status(state.character)

    # Log the mechanical change
    action = "added" if now_active else "cleared"
    state.session.add_mechanical(
        f"Debility {action}: {debility.capitalize()} "
        f"(momentum max {state.character.momentum_max}, reset {state.character.momentum_reset})"
    )


def _show_debilities(state: GameState) -> None:
    display.debility_status(state.character)
