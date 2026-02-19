"""Guide command — interactive gameplay loop helper."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel

from soloquest.commands.guided_mode import start_guided_mode, stop_guided_mode
from soloquest.ui import display
from soloquest.ui.theme import (
    BORDER_REFERENCE,
    FEEDBACK_ERROR,
    FEEDBACK_SUCCESS,
    FEEDBACK_WARN,
    HINT_COMMAND,
    OUTCOME_MISS,
    OUTCOME_STRONG,
    OUTCOME_WEAK,
)

if TYPE_CHECKING:
    from soloquest.loop import GameState

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_guide_prose() -> dict[str, dict[str, str]]:
    with open(_DATA_DIR / "guide.toml", "rb") as f:
        return tomllib.load(f)


_GUIDE = _load_guide_prose()


def handle_guide(state: GameState, args: list[str], flags: set[str]) -> None:
    """Interactive guide for the Ironsworn: Starforged game loop.

    Shows the core gameplay loop and provides contextual suggestions.
    Usage:
        /guide - Show game loop overview
        /guide [step] - Show help for specific step (envision, oracle, move, outcome)
        /guide start - Enter guided mode (step-by-step wizard)
        /guide stop - Exit guided mode
    """
    if args and args[0].lower() == "start":
        start_guided_mode(state)
        return

    if args and args[0].lower() == "stop":
        stop_guided_mode(state)
        return

    if args and args[0].lower() in ["envision", "oracle", "move", "outcome"]:
        _show_step_detail(args[0].lower(), state)
        return

    _show_game_loop(state)


def _show_game_loop(state: GameState) -> None:
    """Display the complete game loop overview."""
    display.rule("Ironsworn: Starforged Game Loop")
    display.console.print()

    # The game loop flowchart
    display.console.print(f"  [bold {HINT_COMMAND}]START[/bold {HINT_COMMAND}]")
    display.console.print("    |")
    display.console.print("    v")
    display.console.print()

    display.console.print("  [bold]1. ENVISION[/bold] the current situation")
    display.console.print("     [dim]Write what your character is doing[/dim]")
    display.console.print(
        f"     [{HINT_COMMAND}]> Type narrative text (no / prefix)[/{HINT_COMMAND}]"
    )
    display.console.print()
    display.console.print("     <-->")
    display.console.print()
    display.console.print("  [bold]2. ASK THE ORACLE[/bold] when uncertain")
    display.console.print("     [dim]Get answers about the situation, location, NPCs[/dim]")
    display.console.print(
        f"     [{HINT_COMMAND}]> /oracle [table] (e.g., /oracle action theme)[/{HINT_COMMAND}]"
    )
    display.console.print()
    display.console.print("    |")
    display.console.print("    v")
    display.console.print()
    display.console.print("  [bold]3. MAKE A MOVE[/bold] when action triggers it")
    display.console.print("     [dim]Roll dice to resolve risky actions[/dim]")
    display.console.print(
        f"     [{HINT_COMMAND}]> /move [name] (e.g., /move face danger)[/{HINT_COMMAND}]"
    )
    display.console.print()
    display.console.print("    |")
    display.console.print("    v")
    display.console.print()

    # Outcomes section with color coding
    display.console.print("  [bold]OUTCOMES:[/bold]")
    display.console.print()
    display.console.print(
        f"    [{OUTCOME_STRONG}]STRONG HIT[/{OUTCOME_STRONG}] [{OUTCOME_STRONG}][OK OK][/{OUTCOME_STRONG}]"
    )
    display.console.print("      You succeeded and are in control")
    display.console.print("      > What do [bold]you[/bold] do next?")
    display.console.print()
    display.console.print(
        f"    [{OUTCOME_WEAK}]WEAK HIT[/{OUTCOME_WEAK}] [{OUTCOME_WEAK}][OK NO][/{OUTCOME_WEAK}]"
    )
    display.console.print("      You succeeded with a lesser result or cost")
    display.console.print("      > What [bold]happens[/bold] next?")
    display.console.print()
    display.console.print(
        f"    [{OUTCOME_MISS}]MISS[/{OUTCOME_MISS}] [{OUTCOME_MISS}][NO NO][/{OUTCOME_MISS}]"
    )
    display.console.print("      You failed or face a dramatic turn of events")
    display.console.print("      > What [bold]happens[/bold] next?")
    display.console.print()
    display.console.print("  [dim]> Loop back to step 1 (Envision)[/dim]")
    display.console.print()
    display.rule()
    display.console.print()

    # Contextual suggestions based on game state
    _show_contextual_suggestions(state)

    display.console.print()
    display.console.print("  [dim]For detailed help on each step:[/dim]")
    display.console.print(
        f"    [{HINT_COMMAND}]/guide envision[/{HINT_COMMAND}]  — Learn about envisioning"
    )
    display.console.print(
        f"    [{HINT_COMMAND}]/guide oracle[/{HINT_COMMAND}]    — Learn about oracles"
    )
    display.console.print(
        f"    [{HINT_COMMAND}]/guide move[/{HINT_COMMAND}]      — Learn about moves"
    )
    display.console.print(
        f"    [{HINT_COMMAND}]/guide outcome[/{HINT_COMMAND}]   — Learn about outcomes"
    )
    display.console.print()


def _show_contextual_suggestions(state: GameState) -> None:
    """Show suggestions based on current game state."""
    display.console.print("  [bold]SUGGESTIONS FOR YOU RIGHT NOW:[/bold]")
    display.console.print()

    # Check if there are active vows
    active_vows = [v for v in state.vows if not v.fulfilled]

    if not active_vows:
        display.console.print(f"    • [{FEEDBACK_WARN}]You have no active vows[/{FEEDBACK_WARN}]")
        display.console.print(
            f"      Consider: [{HINT_COMMAND}]/vow [rank] [description][/{HINT_COMMAND}]"
        )
    else:
        display.console.print(f"    • You have {len(active_vows)} active vow(s)")
        if len(state.session.entries) == 0:
            display.console.print("      [dim]Start by describing your current situation[/dim]")

    # Check character state
    if state.character.health <= 2:
        display.console.print(f"    • [{FEEDBACK_ERROR}]Your health is low[/{FEEDBACK_ERROR}]")
        display.console.print(
            f"      Consider: [{HINT_COMMAND}]/move heal[/{HINT_COMMAND}] or [{HINT_COMMAND}]/move resupply[/{HINT_COMMAND}]"
        )

    if state.character.momentum <= 2 and state.character.momentum >= 0:
        display.console.print(f"    • [{FEEDBACK_WARN}]Your momentum is low[/{FEEDBACK_WARN}]")
        display.console.print("      Consider making moves to gain momentum")

    if state.character.supply <= 1:
        display.console.print(
            f"    • [{FEEDBACK_WARN}]Your supplies are running low[/{FEEDBACK_WARN}]"
        )
        display.console.print(f"      Consider: [{HINT_COMMAND}]/move resupply[/{HINT_COMMAND}]")

    # Check session progress
    if len(state.session.entries) == 0:
        display.console.print()
        display.console.print(f"    [{FEEDBACK_SUCCESS}]New session started![/{FEEDBACK_SUCCESS}]")
        display.console.print(
            "    [dim]Begin by describing where you are and what you're doing[/dim]"
        )


def _show_step_detail(step: str, state: GameState) -> None:
    """Show detailed help for a specific step of the game loop."""
    if step == "envision":
        _show_envision_help(state)
    elif step == "oracle":
        _show_oracle_help(state)
    elif step == "move":
        _show_move_help(state)
    elif step == "outcome":
        _show_outcome_help(state)


def _show_step_help(step: str, state: GameState, **format_kwargs: int) -> None:
    """Show detailed help for a gameplay step, loaded from guide.toml."""
    section = _GUIDE[step]
    display.rule(section["title"])
    display.console.print()
    content = section["content"].format(**format_kwargs)
    display.console.print(Panel(content, border_style=BORDER_REFERENCE, padding=(1, 2)))
    display.console.print()


def _show_envision_help(state: GameState) -> None:
    _show_step_help("envision", state)


def _show_oracle_help(state: GameState) -> None:
    _show_step_help("oracle", state, oracle_count=len(state.oracles))


def _show_move_help(state: GameState) -> None:
    _show_step_help("move", state, move_count=len(state.moves))


def _show_outcome_help(state: GameState) -> None:
    _show_step_help("outcome", state)
