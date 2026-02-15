"""Character display and track adjustment commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starforged.engine.dice import DiceMode, make_dice_provider
from starforged.ui import display

if TYPE_CHECKING:
    from starforged.loop import GameState

TRACKS = {"health", "spirit", "supply"}


def handle_char(state: GameState, args: list[str], flags: set[str]) -> None:
    display.character_sheet(
        state.character,
        state.vows,
        session_count=state.session_count,
        dice_mode=state.dice_mode.value,
    )


def handle_track(state: GameState, track: str, args: list[str]) -> None:
    """Handle /health, /spirit, /supply with +N or -N."""
    if not args:
        val = getattr(state.character, track)
        display.info(f"  {track.capitalize()}: {val}/5")
        return

    raw = args[0]
    try:
        delta = int(raw)
    except ValueError:
        display.error(f"Usage: /{track} +N or -{track} N  (e.g. /{track} +1)")
        return

    new_val = state.character.adjust_track(track, delta)
    display.mechanical_update(f"{track.capitalize()} {delta:+d} → {new_val}/5")
    state.session.add_mechanical(f"{track.capitalize()} {delta:+d} (now {new_val}/5)")


def handle_momentum(state: GameState, args: list[str], flags: set[str]) -> None:
    if not args:
        display.info(f"  Momentum: {state.character.momentum:+d}")
        return

    raw = args[0]
    try:
        delta = int(raw)
    except ValueError:
        display.error("Usage: /momentum +N or -N")
        return

    new_val = state.character.adjust_momentum(delta)
    display.mechanical_update(f"Momentum {delta:+d} → {new_val:+d}")
    state.session.add_mechanical(f"Momentum {delta:+d} (now {new_val:+d})")


def handle_settings(state: GameState, args: list[str], flags: set[str]) -> None:
    if not args:
        display.info(f"  Dice mode: {state.dice_mode.value}")
        display.info("  Usage: /settings dice [digital|physical|mixed]")
        return

    if args[0] == "dice" and len(args) >= 2:
        mode_raw = args[1].lower()
        try:
            new_mode = DiceMode(mode_raw)
        except ValueError:
            display.error(f"Unknown dice mode '{mode_raw}'. Options: digital, physical, mixed")
            return

        state.dice_mode = new_mode
        state.dice = make_dice_provider(new_mode)
        display.success(f"Dice mode set to: {new_mode.value}")
        state.session.add_mechanical(f"Dice mode changed to {new_mode.value}")
    else:
        display.error("Usage: /settings dice [digital|physical|mixed]")
