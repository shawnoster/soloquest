"""Guided mode handlers - step-by-step gameplay wizard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prompt_toolkit.formatted_text import HTML
from rich.prompt import Confirm, Prompt

from wyrd.ui import display
from wyrd.ui.theme import FEEDBACK_SUCCESS, HINT_COMMAND, MECHANIC_GUTTER, ORACLE_GUTTER

if TYPE_CHECKING:
    from wyrd.loop import GameState

# Normal gameplay loop phases
_NORMAL_PHASES = ["envision", "oracle", "move", "outcome"]

# Sector creation wizard phases (Steps 2–11 from rulebook pp. 114–126)
# Region (Step 1) is captured interactively at wizard start.
SECTOR_PHASES = [
    "sector_settlements",  # Steps 2+3: count + generate each settlement
    "sector_planets",  # Step 4: planet class for planetside/orbital
    "sector_stars",  # Step 5: stellar object (optional)
    "sector_map",  # Step 6: sketch the hex map
    "sector_passages",  # Step 7: draw passage routes
    "sector_zoom",  # Step 8: zoom in on one settlement
    "sector_connection",  # Step 9: create a local connection
    "sector_trouble",  # Step 10: introduce sector trouble
    "sector_name",  # Step 11: name the sector
]

_SETTLEMENTS_BY_REGION = {"terminus": 4, "outlands": 3, "expanse": 2}
_PASSAGES_BY_REGION = {"terminus": 3, "outlands": 2, "expanse": 1}


def start_guided_mode(state: GameState, mode: str = "normal") -> None:
    """Enter guided mode. mode='normal' for gameplay loop, mode='sector' for sector wizard."""
    if mode == "sector":
        _start_sector_wizard(state)
    else:
        _start_normal_guided(state)


def _start_normal_guided(state: GameState) -> None:
    """Enter the standard envision→oracle→move→outcome guided loop."""
    state.guided_mode = True
    state.guided_phase = "envision"

    display.rule("Guided Mode Started")
    display.console.print()
    display.console.print(f"  [{FEEDBACK_SUCCESS}]Welcome to Guided Mode![/{FEEDBACK_SUCCESS}]")
    display.console.print()
    display.console.print("  I'll walk you through the game loop step by step.")
    display.console.print(
        f"  Your current phase will show in the prompt: [{HINT_COMMAND}][[ENVISION]] >[/{HINT_COMMAND}]"
    )
    display.console.print()
    display.console.print("  [dim]Commands in guided mode:[/dim]")
    display.console.print(f"    [{HINT_COMMAND}]/guide stop[/{HINT_COMMAND}] - Exit guided mode")
    display.console.print(f"    [{HINT_COMMAND}]/next[/{HINT_COMMAND}] - Advance to next phase")
    display.console.print(f"    [{HINT_COMMAND}]/help[/{HINT_COMMAND}] - Show available commands")
    display.console.print()
    display.console.print("  " + "-" * 76)
    display.console.print()

    _show_phase_help(state)


def _start_sector_wizard(state: GameState) -> None:
    """Enter the Build a Starting Sector wizard (pp. 114–126)."""
    display.rule("Build a Starting Sector")
    display.console.print()
    display.console.print(
        f"  [{FEEDBACK_SUCCESS}]Starting sector creation wizard![/{FEEDBACK_SUCCESS}]"
    )
    display.console.print()
    display.console.print("  This wizard walks you through all 11 steps (pp. 114–126).")
    display.console.print("  Allow about 30–45 minutes.")
    display.console.print()
    display.console.print("  [dim]Commands:[/dim]")
    display.console.print(
        f"    [{HINT_COMMAND}]/next[/{HINT_COMMAND}]       — Advance to next step"
    )
    display.console.print(f"    [{HINT_COMMAND}]/guide stop[/{HINT_COMMAND}] — Exit wizard")
    display.console.print()

    # Step 1: Choose region interactively
    display.console.print("  [bold cyan]STEP 1: CHOOSE YOUR STARTING REGION[/bold cyan]")
    display.console.print()
    display.console.print("  [bold]Terminus[/bold]  — Settled space, well-charted routes")
    display.console.print("  [bold]Outlands[/bold]  — Frontier, scattered and perilous")
    display.console.print("  [bold]Expanse[/bold]   — Deep unknown, lonely exploration")
    display.console.print()

    try:
        region = Prompt.ask(
            "  Choose region",
            choices=["terminus", "outlands", "expanse"],
            default="terminus",
        )
    except (KeyboardInterrupt, EOFError):
        display.info("Sector wizard cancelled.")
        return

    state.guided_mode = True
    state.guided_phase = "sector_settlements"
    state.sector_region = region

    display.console.print()
    display.console.print(
        f"  [{FEEDBACK_SUCCESS}]Region set: {region.capitalize()}[/{FEEDBACK_SUCCESS}]"
    )
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
            state.sector_region = None
            display.success("Guided mode stopped. You're back to normal play.")
            display.console.print()
        else:
            display.info("Staying in guided mode.")
    except (KeyboardInterrupt, EOFError):
        display.console.print()
        display.info("Staying in guided mode.")


def get_guided_prompt(state: GameState) -> str:
    """Get the prompt string with phase indicator (plain text for testing)."""
    if not state.guided_mode:
        return "> "

    phase_display = state.guided_phase.upper().replace("SECTOR_", "")
    return f"[{phase_display}] > "


def get_guided_prompt_html(state: GameState) -> HTML:
    """Get the prompt with HTML-style formatting for prompt_toolkit."""
    if not state.guided_mode:
        return HTML("> ")

    color_map = {
        "envision": "cyan",
        "oracle": "magenta",
        "move": "yellow",
        "outcome": "green",
        # Sector phases all get amber/brightyellow
        "sector_settlements": "ansibrightyellow",
        "sector_planets": "ansibrightyellow",
        "sector_stars": "ansibrightyellow",
        "sector_map": "ansibrightyellow",
        "sector_passages": "ansibrightyellow",
        "sector_zoom": "ansibrightyellow",
        "sector_connection": "ansibrightyellow",
        "sector_trouble": "ansibrightyellow",
        "sector_name": "ansibrightyellow",
    }

    color = color_map.get(state.guided_phase, "white")
    phase_display = state.guided_phase.upper().replace("SECTOR_", "")

    return HTML(
        f"<ansibrightblue>▌</ansibrightblue>\n<ansibrightblue>▌</ansibrightblue> <{color}>[{phase_display}]</{color}> "
    )


def advance_phase(state: GameState) -> None:
    """Advance to the next phase in the active game loop or sector wizard."""
    if not state.guided_mode:
        display.error("You're not in guided mode. Use /guide start to enter guided mode.")
        return

    if state.guided_phase in SECTOR_PHASES:
        _advance_sector_phase(state)
    else:
        _advance_normal_phase(state)


def _advance_normal_phase(state: GameState) -> None:
    current_index = _NORMAL_PHASES.index(state.guided_phase)
    next_index = (current_index + 1) % len(_NORMAL_PHASES)
    state.guided_phase = _NORMAL_PHASES[next_index]

    display.console.print()
    display.success(f"Advanced to: {state.guided_phase.upper()}")
    display.console.print()
    _show_phase_help(state)


def _advance_sector_phase(state: GameState) -> None:
    current_index = SECTOR_PHASES.index(state.guided_phase)
    next_index = current_index + 1

    if next_index >= len(SECTOR_PHASES):
        # All steps done
        display.console.print()
        display.rule("Sector Creation Complete")
        display.console.print()
        display.console.print(
            f"  [{FEEDBACK_SUCCESS}]Your starting sector is ready![/{FEEDBACK_SUCCESS}]"
        )
        display.console.print()
        display.console.print("  Next steps:")
        display.console.print("    • Jump to p. 128 to begin your first adventure")
        display.console.print("    • Use [cyan]/vow[/cyan] to swear your first iron vow")
        display.console.print("    • Use [cyan]/guide[/cyan] to review the core gameplay loop")
        display.console.print()
        state.guided_mode = False
        state.guided_phase = "envision"
        state.sector_region = None
    else:
        state.guided_phase = SECTOR_PHASES[next_index]
        display.console.print()
        display.success(f"Step {next_index + 2} of 11")
        display.console.print()
        _show_phase_help(state)


def _show_phase_help(state: GameState) -> None:
    """Show contextual help for the current phase."""
    phase = state.guided_phase

    if phase in SECTOR_PHASES:
        _show_sector_phase_help(state)
        return

    # Normal gameplay loop phases
    if phase == "envision":
        display.console.print(f"  [bold {HINT_COMMAND}]PHASE: ENVISION[/bold {HINT_COMMAND}]")
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
            f"  [dim]When done, type [{HINT_COMMAND}]/next[/{HINT_COMMAND}] to move to ORACLE phase[/dim]"
        )
        display.console.print()

    elif phase == "oracle":
        display.console.print(f"  [bold {ORACLE_GUTTER}]PHASE: ORACLE[/bold {ORACLE_GUTTER}]")
        display.console.print()
        display.console.print("  [bold]What to do:[/bold]")
        display.console.print("    • Ask questions about uncertain details")
        display.console.print(
            f"    • Use [{HINT_COMMAND}]/oracle [[table]][/{HINT_COMMAND}] to get answers"
        )
        display.console.print("    • Common oracles: action theme, descriptor, character")
        display.console.print()
        display.console.print("  [dim]Example:[/dim]")
        display.console.print("  [dim]> /oracle action theme[/dim]")
        display.console.print()
        display.console.print(
            f"  [dim]When done, type [{HINT_COMMAND}]/next[/{HINT_COMMAND}] to move to MOVE phase[/dim]"
        )
        display.console.print()
        display.console.print(
            f"  [dim]Or type [{HINT_COMMAND}]/next[/{HINT_COMMAND}] now to skip if no questions[/dim]"
        )
        display.console.print()

    elif phase == "move":
        display.console.print(f"  [bold {MECHANIC_GUTTER}]PHASE: MOVE[/bold {MECHANIC_GUTTER}]")
        display.console.print()
        display.console.print("  [bold]What to do:[/bold]")
        display.console.print("    • Make a move when taking risky action")
        display.console.print(
            f"    • Use [{HINT_COMMAND}]/move [[name]][/{HINT_COMMAND}] to resolve"
        )
        display.console.print("    • Common moves: face danger, strike, gather information")
        display.console.print()
        display.console.print("  [dim]Example:[/dim]")
        display.console.print("  [dim]> /move face danger[/dim]")
        display.console.print()
        display.console.print(
            f"  [dim]After your move, type [{HINT_COMMAND}]/next[/{HINT_COMMAND}] to move to OUTCOME phase[/dim]"
        )
        display.console.print()

    elif phase == "outcome":
        display.console.print(
            f"  [bold {FEEDBACK_SUCCESS}]PHASE: OUTCOME[/bold {FEEDBACK_SUCCESS}]"
        )
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
            f"  [dim]When done, type [{HINT_COMMAND}]/next[/{HINT_COMMAND}] to return to ENVISION[/dim]"
        )
        display.console.print()


def _show_sector_phase_help(state: GameState) -> None:
    """Show help for the current sector wizard phase."""
    phase = state.guided_phase
    region = state.sector_region or "outlands"
    settlement_count = _SETTLEMENTS_BY_REGION.get(region, 3)
    passage_count = _PASSAGES_BY_REGION.get(region, 2)
    pop_key = f"population_{region}"

    c = HINT_COMMAND  # shorthand for color tag

    if phase == "sector_settlements":
        display.console.print(
            "  [bold ansibrightyellow]STEP 2–3: SETTLEMENTS[/bold ansibrightyellow]"
        )
        display.console.print()
        display.console.print(
            f"  Your region ([bold]{region.capitalize()}[/bold]) has "
            f"[bold]{settlement_count}[/bold] settlements."
        )
        display.console.print()
        display.console.print("  For [bold]each[/bold] settlement, roll:")
        display.console.print(f"    [{c}]/oracle settlement_name[/{c}]")
        display.console.print(f"    [{c}]/oracle settlement_location[/{c}]")
        display.console.print(f"    [{c}]/oracle {pop_key}[/{c}]")
        display.console.print(f"    [{c}]/oracle settlement_authority[/{c}]")
        display.console.print(
            f"    [{c}]/oracle settlement_projects[/{c}]  [dim](roll 1–2 times)[/dim]"
        )
        display.console.print()
        display.console.print("  Write each as a short note, e.g.:")
        display.console.print(
            "  [dim]Bleakhold (Orbital) — Pop: Hundreds — Auth: Corrupt — Mining, Black market[/dim]"
        )
        display.console.print()
        display.console.print(
            f"  [dim]When all {settlement_count} are done, type [{c}]/next[/{c}][/dim]"
        )
        display.console.print()

    elif phase == "sector_planets":
        display.console.print("  [bold ansibrightyellow]STEP 4: PLANETS[/bold ansibrightyellow]")
        display.console.print()
        display.console.print(
            "  For each [bold]Planetside[/bold] or [bold]Orbital[/bold] settlement, roll:"
        )
        display.console.print(f"    [{c}]/oracle planet_class[/{c}]")
        display.console.print()
        display.console.print(
            "  Give the planet a name if you like (pp. 308–318 for type-specific names)."
        )
        display.console.print("  Add the planet type to your settlement note.")
        display.console.print()
        display.console.print(f"  [dim]When done, type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_stars":
        display.console.print(
            "  [bold ansibrightyellow]STEP 5: STARS (optional)[/bold ansibrightyellow]"
        )
        display.console.print()
        display.console.print("  For each settlement, you can roll for the star it orbits:")
        display.console.print(f"    [{c}]/oracle stellar_object[/{c}]")
        display.console.print()
        display.console.print(
            "  [dim]A corrupted star or impending supernova can shape your opening situation.[/dim]"
        )
        display.console.print("  [dim]This step is optional — skip with /next if you prefer.[/dim]")
        display.console.print()
        display.console.print(f"  [dim]When done (or skipping), type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_map":
        display.console.print("  [bold ansibrightyellow]STEP 6: SECTOR MAP[/bold ansibrightyellow]")
        display.console.print()
        display.console.print("  Sketch a simple hex grid and place your settlements.")
        display.console.print("  Suggested symbols:")
        display.console.print("    ⊕  Planetside     ⊙  Orbital     □  Deep Space")
        display.console.print()
        display.console.print("  Keep it loose — the map shows connections, not distances.")
        display.console.print("  You'll add passages and more locations as you play.")
        display.console.print()
        display.console.print(f"  [dim]When your sketch is ready, type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_passages":
        display.console.print("  [bold ansibrightyellow]STEP 7: PASSAGES[/bold ansibrightyellow]")
        display.console.print()
        display.console.print(
            f"  Your region ([bold]{region.capitalize()}[/bold]) gets "
            f"[bold]{passage_count}[/bold] passage(s)."
        )
        display.console.print()
        display.console.print("  Draw each passage as a line on your map. Each must either:")
        display.console.print("    • Connect two settlements, or")
        display.console.print("    • Connect a settlement to the sector edge (leading out)")
        display.console.print()
        display.console.print("  [bold yellow]Why this matters:[/bold yellow]")
        display.console.print(
            f"    On a passage  → [{c}]/move set a course[/{c}]  (single roll, faster)"
        )
        display.console.print(
            f"    Off a passage → [{c}]/move undertake an expedition[/{c}]  (harder, earns XP)"
        )
        display.console.print()
        display.console.print(f"  [dim]When your passages are drawn, type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_zoom":
        display.console.print(
            "  [bold ansibrightyellow]STEP 8: ZOOM IN ON A SETTLEMENT[/bold ansibrightyellow]"
        )
        display.console.print()
        display.console.print("  Pick the settlement most interesting to you. Roll:")
        display.console.print(
            f"    [{c}]/oracle settlement_first_look[/{c}]  [dim](roll 1–2 times)[/dim]"
        )
        display.console.print(f"    [{c}]/oracle settlement_trouble[/{c}]")
        display.console.print()
        display.console.print("  If it's Planetside or Orbital, also flesh out the planet:")
        display.console.print(
            f"    [{c}]/oracle descriptor focus[/{c}]  [dim](atmosphere, feature, hazard)[/dim]"
        )
        display.console.print()
        display.console.print("  Note anything evocative in your journal.")
        display.console.print()
        display.console.print(f"  [dim]When done, type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_connection":
        display.console.print(
            "  [bold ansibrightyellow]STEP 9: LOCAL CONNECTION[/bold ansibrightyellow]"
        )
        display.console.print()
        display.console.print(
            "  [bold green]Make a Connection is an automatic strong hit — no dice needed.[/bold green]"
        )
        display.console.print()
        display.console.print("  Roll to build out your starting connection:")
        display.console.print(
            f"    [{c}]/oracle given_name[/{c}]              [dim]— their name[/dim]"
        )
        display.console.print(
            f"    [{c}]/oracle role[/{c}]                   [dim]— their role or expertise[/dim]"
        )
        display.console.print(
            f"    [{c}]/oracle character_goal[/{c}]         [dim]— what do they want?[/dim]"
        )
        display.console.print(
            f"    [{c}]/oracle character_first_look[/{c}]   [dim]— how do they present?[/dim]"
        )
        display.console.print(
            f"    [{c}]/oracle character_aspect[/{c}]       [dim]— a revealed trait (optional)[/dim]"
        )
        display.console.print()
        display.console.print("  Then decide:")
        display.console.print(
            "    • Rank: Troublesome or Dangerous (right for a starting connection)"
        )
        display.console.print("    • Home: which settlement do they live in?")
        display.console.print()
        display.console.print("  Note them in your journal or connections worksheet.")
        display.console.print()
        display.console.print(f"  [dim]When done, type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_trouble":
        display.console.print(
            "  [bold ansibrightyellow]STEP 10: SECTOR TROUBLE[/bold ansibrightyellow]"
        )
        display.console.print()
        display.console.print("  Roll for the sector-wide threat or shadow:")
        display.console.print(f"    [{c}]/oracle sector_trouble[/{c}]")
        display.console.print()
        display.console.print("  Envision how this trouble manifests in your sector.")
        display.console.print("  Note it in your journal — it may drive your first vow.")
        display.console.print()
        display.console.print(f"  [dim]When done, type [{c}]/next[/{c}][/dim]")
        display.console.print()

    elif phase == "sector_name":
        display.console.print(
            "  [bold ansibrightyellow]STEP 11: NAME THE SECTOR[/bold ansibrightyellow]"
        )
        display.console.print()
        display.console.print("  Roll both and combine:")
        display.console.print(f"    [{c}]/oracle sector_name_prefix sector_name_suffix[/{c}]")
        display.console.print()
        display.console.print('  [dim]Example: Fallen + Maw → "The Fallen Maw"[/dim]')
        display.console.print('  [dim]Example: Crimson + Drift → "Crimson Drift"[/dim]')
        display.console.print()
        display.console.print("  Write the name on your sector map.")
        display.console.print()
        display.console.print(
            f"  [dim]When done, type [{c}]/next[/{c}] to complete sector creation[/dim]"
        )
        display.console.print()


def handle_guided_action(state: GameState, line: str) -> None:
    """Handle special guided mode actions based on context."""
    pass
