"""Character display and track adjustment commands."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.prompt import Confirm

from soloquest.commands.new_character import run_new_character_flow
from soloquest.engine.dice import DiceMode, make_dice_provider
from soloquest.state.save import save_game
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState

TRACKS = {"health", "spirit", "supply"}


def handle_char(state: GameState, args: list[str], flags: set[str]) -> None:
    if args and args[0] == "new":
        _handle_char_new(state)
        return
    display.character_sheet(
        state.character,
        state.vows,
        session_count=state.session_count,
        assets=state.assets,
    )


def _handle_char_new(state: GameState) -> None:
    display.info("Create a new character alongside the current one.")
    try:
        if not Confirm.ask("  Continue?", default=False):
            return
    except (KeyboardInterrupt, EOFError):
        return

    data_dir = Path(__file__).parent.parent / "data"
    result = run_new_character_flow(data_dir, state.truth_categories, include_truths=False)
    if result is None:
        display.info("New character creation cancelled.")
        return

    character, vows, dice_mode = result
    state.character = character
    state.vows = vows
    state.session_count = 0
    state.session = None
    state.dice_mode = dice_mode
    state.dice = make_dice_provider(dice_mode)
    save_game(character, vows, 0, dice_mode)
    display.success(f"Character created: {character.name}. Switching to them now.")


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
        from soloquest.config import config

        display.info(f"  Adventures directory: {config.adventures_dir}")
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
