"""Guide command — interactive gameplay loop helper."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def handle_guide(state: GameState, args: list[str], flags: set[str]) -> None:
    """Interactive guide for the Ironsworn: Starforged game loop.

    Shows the core gameplay loop and provides contextual suggestions.
    Usage: /guide [step] where step is: envision, oracle, move, outcome
    """
    if args and args[0].lower() in ["envision", "oracle", "move", "outcome"]:
        _show_step_detail(args[0].lower(), state)
        return

    _show_game_loop(state)


def _show_game_loop(state: GameState) -> None:
    """Display the complete game loop overview."""
    display.rule("Ironsworn: Starforged Game Loop")
    display.console.print()

    # The game loop flowchart
    display.console.print("  [bold cyan]START[/bold cyan]")
    display.console.print("    |")
    display.console.print("    v")
    display.console.print()

    display.console.print("  [bold]1. ENVISION[/bold] the current situation")
    display.console.print("     [dim]Write what your character is doing[/dim]")
    display.console.print("     [cyan]> Type narrative text (no / prefix)[/cyan]")
    display.console.print()
    display.console.print("     <-->")
    display.console.print()
    display.console.print("  [bold]2. ASK THE ORACLE[/bold] when uncertain")
    display.console.print("     [dim]Get answers about the situation, location, NPCs[/dim]")
    display.console.print("     [cyan]> /oracle [table] (e.g., /oracle action theme)[/cyan]")
    display.console.print()
    display.console.print("    |")
    display.console.print("    v")
    display.console.print()
    display.console.print("  [bold]3. MAKE A MOVE[/bold] when action triggers it")
    display.console.print("     [dim]Roll dice to resolve risky actions[/dim]")
    display.console.print("     [cyan]> /move [name] (e.g., /move face danger)[/cyan]")
    display.console.print()
    display.console.print("    |")
    display.console.print("    v")
    display.console.print()

    # Outcomes section with color coding
    display.console.print("  [bold]OUTCOMES:[/bold]")
    display.console.print()
    display.console.print("    [bold blue]STRONG HIT[/bold blue] [blue][OK OK][/blue]")
    display.console.print("      You succeeded and are in control")
    display.console.print("      > What do [bold]you[/bold] do next?")
    display.console.print()
    display.console.print("    [bold magenta]WEAK HIT[/bold magenta] [magenta][OK NO][/magenta]")
    display.console.print("      You succeeded with a lesser result or cost")
    display.console.print("      > What [bold]happens[/bold] next?")
    display.console.print()
    display.console.print("    [bold red]MISS[/bold red] [red][NO NO][/red]")
    display.console.print("      You failed or face a dramatic turn of events")
    display.console.print("      > What [bold]happens[/bold] next?")
    display.console.print()
    display.console.print("  [dim]> Loop back to step 1 (Envision)[/dim]")
    display.console.print()
    display.console.print("  " + "-" * 76)
    display.console.print()

    # Contextual suggestions based on game state
    _show_contextual_suggestions(state)

    display.console.print()
    display.console.print("  [dim]For detailed help on each step:[/dim]")
    display.console.print("    [cyan]/guide envision[/cyan]  — Learn about envisioning")
    display.console.print("    [cyan]/guide oracle[/cyan]    — Learn about oracles")
    display.console.print("    [cyan]/guide move[/cyan]      — Learn about moves")
    display.console.print("    [cyan]/guide outcome[/cyan]   — Learn about outcomes")
    display.console.print()


def _show_contextual_suggestions(state: GameState) -> None:
    """Show suggestions based on current game state."""
    display.console.print("  [bold]SUGGESTIONS FOR YOU RIGHT NOW:[/bold]")
    display.console.print()

    # Check if there are active vows
    active_vows = [v for v in state.vows if not v.fulfilled]

    if not active_vows:
        display.console.print("    • [yellow]You have no active vows[/yellow]")
        display.console.print("      Consider: [cyan]/vow [rank] [description][/cyan]")
    else:
        display.console.print(f"    • You have {len(active_vows)} active vow(s)")
        if len(state.session.entries) == 0:
            display.console.print("      [dim]Start by describing your current situation[/dim]")

    # Check character state
    if state.character.health <= 2:
        display.console.print("    • [red]Your health is low[/red]")
        display.console.print(
            "      Consider: [cyan]/move heal[/cyan] or [cyan]/move resupply[/cyan]"
        )

    if state.character.momentum <= 2 and state.character.momentum >= 0:
        display.console.print("    • [yellow]Your momentum is low[/yellow]")
        display.console.print("      Consider making moves to gain momentum")

    if state.character.supply <= 1:
        display.console.print("    • [yellow]Your supplies are running low[/yellow]")
        display.console.print("      Consider: [cyan]/move resupply[/cyan]")

    # Check session progress
    if len(state.session.entries) == 0:
        display.console.print()
        display.console.print("    [bold green]New session started![/bold green]")
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


def _show_envision_help(state: GameState) -> None:
    """Show detailed help for the Envision step."""
    display.rule("Step 1: Envision the Current Situation")
    display.console.print()

    content = """[bold]ENVISION[/bold] means describing the fiction — what's happening in your story.

[bold cyan]What to do:[/bold cyan]
  • Describe what your character sees, hears, and experiences
  • Write about what your character is doing or attempting
  • Add details about the environment, NPCs, or situation
  • Follow up on the results of your last move

[bold cyan]How to do it:[/bold cyan]
  • Just type — no command prefix needed
  • Your words become your journal entries
  • Write as much or as little as you want

[bold cyan]Example:[/bold cyan]
  > I push through the airlock into the derelict station.
  > Emergency lights flicker. The air smells of rust and decay.
  > I need to find the main computer core to recover the data.

[bold yellow]Tips:[/bold yellow]
  • Fiction comes first — always describe before rolling
  • When uncertain about details, use [cyan]/oracle[/cyan] to answer questions
  • When you take risky action, use [cyan]/move[/cyan] to resolve it
"""

    display.console.print(Panel(content, border_style="cyan", padding=(1, 2)))
    display.console.print()


def _show_oracle_help(state: GameState) -> None:
    """Show detailed help for the Oracle step."""
    display.rule("Step 2: Ask the Oracle")
    display.console.print()

    content = f"""[bold]ASK THE ORACLE[/bold] when you need answers about the world.

[bold cyan]When to use:[/bold cyan]
  • You're uncertain about a detail in the fiction
  • You need to know what happens next
  • You want inspiration for NPCs, locations, or events
  • You need a yes/no answer to a question

[bold cyan]How to do it:[/bold cyan]
  [cyan]/oracle [table names][/cyan]

[bold cyan]Common oracles:[/bold cyan]
  • [cyan]/oracle action theme[/cyan] — Creative prompt pair
  • [cyan]/oracle descriptor[/cyan] — Single descriptive word
  • [cyan]/oracle character name[/cyan] — NPC name
  • [cyan]/oracle character role[/cyan] — NPC role/profession
  • [cyan]/oracle location[/cyan] — Location descriptor
  • [cyan]/oracle yes no[/cyan] — Yes/no question (use odds like: likely, unlikely)

[bold cyan]Available oracle tables:[/bold cyan] {len(state.oracles)}
  Type [cyan]/help oracles[/cyan] to see all tables

[bold yellow]Tips:[/bold yellow]
  • Ask specific questions, let the oracle answer
  • Combine results creatively (e.g., "Violent" + "Refuge")
  • Trust your first interpretation
  • You can roll multiple oracles at once
"""

    display.console.print(Panel(content, border_style="magenta", padding=(1, 2)))
    display.console.print()


def _show_move_help(state: GameState) -> None:
    """Show detailed help for the Move step."""
    display.rule("Step 3: Make a Move")
    display.console.print()

    content = f"""[bold]MAKE A MOVE[/bold] when your action or the situation triggers it.

[bold cyan]When to use:[/bold cyan]
  • You attempt something risky or uncertain
  • The fiction naturally triggers a move
  • You take action that could fail

[bold cyan]How to do it:[/bold cyan]
  [cyan]/move [name][/cyan]

  Example: [cyan]/move face danger[/cyan]

[bold cyan]Common moves:[/bold cyan]
  • [cyan]/move face danger[/cyan] — Overcome obstacle with skill/stat
  • [cyan]/move gather information[/cyan] — Investigate or research
  • [cyan]/move secure an advantage[/cyan] — Prepare or gain position
  • [cyan]/move strike[/cyan] — Attack in combat
  • [cyan]/move clash[/cyan] — Fight back in combat
  • [cyan]/move make camp[/cyan] — Rest and recover

[bold cyan]Available moves:[/bold cyan] {len(state.moves)}
  Type [cyan]/help moves[/cyan] to see all moves

[bold cyan]How moves work:[/bold cyan]
  1. Choose your stat (Edge, Heart, Iron, Shadow, Wits)
  2. Roll action die (d6) + stat + any bonuses
  3. Compare to two challenge dice (d10s)
  4. Outcome determines what happens next

[bold yellow]Tips:[/bold yellow]
  • Read the move text carefully
  • Choose the most relevant stat for the situation
  • Don't roll unless the move triggers
  • Follow the outcome text for results
"""

    display.console.print(Panel(content, border_style="yellow", padding=(1, 2)))
    display.console.print()


def _show_outcome_help(state: GameState) -> None:
    """Show detailed help for understanding outcomes."""
    display.rule("Step 4: Interpret Outcomes")
    display.console.print()

    content = """[bold]OUTCOMES[/bold] determine what happens after you make a move.

[bold blue]STRONG HIT[/bold blue] [blue]✓✓[/blue]
  • Your action score beats BOTH challenge dice
  • You succeeded and are in control
  • You get what you wanted
  • [bold]You[/bold] decide what happens next
  • Often gain +1 momentum

[bold magenta]WEAK HIT[/bold magenta] [magenta]✓✗[/magenta]
  • Your action score beats ONE challenge die
  • You succeeded, but with a cost or complication
  • You get what you wanted, but...
  • The [bold]situation[/bold] complicates
  • Follow the move's weak hit text

[bold red]MISS[/bold red] [red]✗✗[/red]
  • Your action score beats NEITHER challenge die
  • You failed or face a dramatic turn
  • Things get worse
  • Pay the Price (lose resources, face danger)
  • The [bold]fiction[/bold] determines what happens

[bold yellow]MATCH[/bold yellow] (Challenge dice are equal)
  • Something unexpected happens
  • Twist, opportunity, or complication
  • Works with any outcome type
  • Add dramatic flair to the result

[bold cyan]After an outcome:[/bold cyan]
  1. Read the move's outcome text
  2. Describe what happens in the fiction
  3. Adjust any tracks ([cyan]/health, /momentum, /supply[/cyan], etc.)
  4. Return to Step 1: Envision what happens next

[bold yellow]Tips:[/bold yellow]
  • Always describe the outcome in the fiction first
  • Mechanical effects follow fictional description
  • Weak hits and misses drive the story forward
  • Momentum burn ([cyan]/burn[/cyan]) can upgrade outcomes
"""

    display.console.print(Panel(content, border_style="green", padding=(1, 2)))
    display.console.print()


def _show_quick_start(state: GameState) -> None:
    """Show a quick start guide for new players."""
    display.rule("Quick Start Guide")
    display.console.print()

    display.console.print("  [bold]Welcome to Ironsworn: Starforged![/bold]")
    display.console.print()
    display.console.print("  [bold cyan]Your first steps:[/bold cyan]")
    display.console.print()
    display.console.print("  1. [bold]Describe your scene[/bold]")
    display.console.print("     Type: [dim]I'm investigating an abandoned mining outpost...[/dim]")
    display.console.print()
    display.console.print("  2. [bold]When uncertain, ask the oracle[/bold]")
    display.console.print("     Type: [cyan]/oracle action theme[/cyan]")
    display.console.print()
    display.console.print("  3. [bold]When taking risky action, make a move[/bold]")
    display.console.print("     Type: [cyan]/move face danger[/cyan]")
    display.console.print()
    display.console.print("  4. [bold]Follow the outcome and keep playing[/bold]")
    display.console.print("     Describe what happens and return to step 1")
    display.console.print()
    display.console.print("  [dim]Type [cyan]/guide[/cyan] anytime to see the full game loop[/dim]")
    display.console.print()
