"""Guided mode handlers - step-by-step gameplay wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.formatted_text import HTML
from rich.prompt import Confirm

from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def start_guided_mode(state: GameState) -> None:
    """Enter guided mode - a step-by-step wizard through the game loop."""
    state.guided_mode = True
    state.guided_phase = "envision"

    display.rule("Guided Mode Started")
    display.console.print()
    display.console.print("  [bold green]Welcome to Guided Mode![/bold green]")
    display.console.print()
    display.console.print("  I'll walk you through the game loop step by step.")
    display.console.print("  Your current phase will show in the prompt: [cyan][ENVISION] >[/cyan]")
    display.console.print()
    display.console.print("  [dim]Commands in guided mode:[/dim]")
    display.console.print("    [cyan]/guide stop[/cyan] - Exit guided mode")
    display.console.print("    [cyan]/next[/cyan] - Advance to next phase")
    display.console.print("    [cyan]/help[/cyan] - Show available commands")
    display.console.print()
    display.console.print("  " + "-" * 76)
    display.console.print()

    _show_phase_help(state)


def stop_guided_mode(state: GameState) -> None:
    """Exit guided mode with confirmation."""
    if not state.guided_mode:
        display.info("You're not in guided mode.")
        return

    try:
        if Confirm.ask("  Exit guided mode?", default=False):
            state.guided_mode = False
            state.guided_phase = "envision"
            display.success("Guided mode stopped. You're back to normal play.")
            display.console.print()
        else:
            display.info("Staying in guided mode.")
    except (KeyboardInterrupt, EOFError):
        # User pressed Ctrl+C, treat as "no"
        display.console.print()
        display.info("Staying in guided mode.")


def get_guided_prompt(state: GameState) -> str:
    """Get the prompt string with phase indicator (plain text for testing)."""
    if not state.guided_mode:
        return "> "

    phase_display = state.guided_phase.upper()
    return f"[{phase_display}] > "


def get_guided_prompt_html(state: GameState) -> HTML:
    """Get the prompt with HTML-style formatting for prompt_toolkit.

    prompt_toolkit supports HTML-like tags for styling:
    https://python-prompt-toolkit.readthedocs.io/en/master/pages/printing_text.html
    """
    if not state.guided_mode:
        return HTML("> ")

    # Map phases to colors using prompt_toolkit's HTML-style tags
    color_map = {
        "envision": "cyan",
        "oracle": "magenta",
        "move": "yellow",
        "outcome": "green",
    }

    color = color_map.get(state.guided_phase, "white")
    phase_display = state.guided_phase.upper()

    # Use HTML() which prompt_toolkit will render with proper styling
    return HTML(f'<{color}>[{phase_display}]</{color}> > ')


def advance_phase(state: GameState) -> None:
    """Advance to the next phase in the game loop."""
    if not state.guided_mode:
        display.error("You're not in guided mode. Use /guide start to enter guided mode.")
        return

    phase_order = ["envision", "oracle", "move", "outcome"]
    current_index = phase_order.index(state.guided_phase)
    next_index = (current_index + 1) % len(phase_order)
    state.guided_phase = phase_order[next_index]

    display.console.print()
    display.success(f"Advanced to: {state.guided_phase.upper()}")
    display.console.print()
    _show_phase_help(state)


def _show_phase_help(state: GameState) -> None:
    """Show contextual help for the current phase."""
    phase = state.guided_phase

    if phase == "envision":
        display.console.print("  [bold cyan]PHASE: ENVISION[/bold cyan]")
        display.console.print()
        display.console.print("  [bold]What to do:[/bold]")
        display.console.print("    • Describe what your character is doing")
        display.console.print("    • Write about the current situation")
        display.console.print("    • Just type (no command needed)")
        display.console.print()
        display.console.print("  [dim]Example:[/dim]")
        display.console.print("  [dim]> I approach the derelict station cautiously...[/dim]")
        display.console.print()
        display.console.print(
            "  [dim]When done, type [cyan]/next[/cyan] to move to ORACLE phase[/dim]"
        )
        display.console.print()

    elif phase == "oracle":
        display.console.print("  [bold magenta]PHASE: ORACLE[/bold magenta]")
        display.console.print()
        display.console.print("  [bold]What to do:[/bold]")
        display.console.print("    • Ask questions about uncertain details")
        display.console.print("    • Use [cyan]/oracle [table][/cyan] to get answers")
        display.console.print("    • Common oracles: action theme, descriptor, character")
        display.console.print()
        display.console.print("  [dim]Example:[/dim]")
        display.console.print("  [dim]> /oracle action theme[/dim]")
        display.console.print()
        display.console.print(
            "  [dim]When done, type [cyan]/next[/cyan] to move to MOVE phase[/dim]"
        )
        display.console.print()
        display.console.print("  [dim]Or type [cyan]/next[/cyan] now to skip if no questions[/dim]")
        display.console.print()

    elif phase == "move":
        display.console.print("  [bold yellow]PHASE: MOVE[/bold yellow]")
        display.console.print()
        display.console.print("  [bold]What to do:[/bold]")
        display.console.print("    • Make a move when taking risky action")
        display.console.print("    • Use [cyan]/move [name][/cyan] to resolve")
        display.console.print("    • Common moves: face danger, strike, gather information")
        display.console.print()
        display.console.print("  [dim]Example:[/dim]")
        display.console.print("  [dim]> /move face danger[/dim]")
        display.console.print()
        display.console.print(
            "  [dim]After your move, type [cyan]/next[/cyan] to move to OUTCOME phase[/dim]"
        )
        display.console.print()

    elif phase == "outcome":
        display.console.print("  [bold green]PHASE: OUTCOME[/bold green]")
        display.console.print()
        display.console.print("  [bold]What to do:[/bold]")
        display.console.print("    • Describe what happens based on your result")
        display.console.print("    • Strong Hit - you're in control")
        display.console.print("    • Weak Hit - success with cost")
        display.console.print("    • Miss - things get worse")
        display.console.print()
        display.console.print("  [dim]Example:[/dim]")
        display.console.print("  [dim]> I succeed but alert the security systems...[/dim]")
        display.console.print()
        display.console.print(
            "  [dim]When done, type [cyan]/next[/cyan] to return to ENVISION[/dim]"
        )
        display.console.print()


def handle_guided_action(state: GameState, line: str) -> None:
    """Handle special guided mode actions based on context."""
    # This is called from the main loop to provide contextual guidance
    # For now, we just let the normal command system work
    pass
