"""Session management commands — log, note, end."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.prompt import Prompt

from soloquest.journal.exporter import append_to_journal, export_session
from soloquest.models.session import EntryKind
from soloquest.state.save import save_game
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def handle_log(state: GameState, args: list[str], flags: set[str]) -> None:
    """Show the full session log. /log --moves shows only moves, /log --compact skips mechanical."""
    if not state.session.entries:
        display.info("No entries in this session yet.")
        return

    compact = "compact" in flags
    moves_only = "moves" in flags

    display.rule(f"Session {state.session.number} Log")
    for entry in state.session.entries:
        if moves_only and entry.kind not in (EntryKind.MOVE, EntryKind.ORACLE):
            continue
        if compact and entry.kind == EntryKind.MECHANICAL:
            continue
        display.log_entry(entry)
    display.console.print()


def handle_note(state: GameState, args: list[str], flags: set[str]) -> None:
    """Add a scene/NPC note."""
    if not args:
        display.error("Usage: /note [text]")
        return
    text = " ".join(args)
    state.session.add_note(text)
    display.success(f"Note added: {text}")


def handle_end(state: GameState, args: list[str], flags: set[str]) -> None:
    """End the session — save character, export journal."""
    display.rule("End Session")

    # Optional session title
    title = Prompt.ask("  Session title (leave blank to skip)", default="")
    if title:
        state.session.title = title

    # Summary stats
    entries = state.session.entries
    moves_count = sum(1 for e in entries if e.kind == EntryKind.MOVE)
    oracles_count = sum(1 for e in entries if e.kind == EntryKind.ORACLE)
    journal_count = sum(1 for e in entries if e.kind == EntryKind.JOURNAL)
    notes_count = sum(1 for e in entries if e.kind == EntryKind.NOTE)

    active_vows = sum(1 for v in state.vows if not v.fulfilled)
    fulfilled_vows = sum(1 for v in state.vows if v.fulfilled)

    display.info(f"  Moves rolled:        {moves_count}")
    display.info(f"  Oracles consulted:   {oracles_count}")
    display.info(f"  Journal entries:     {journal_count}")
    if notes_count:
        display.info(f"  Notes:               {notes_count}")
    if fulfilled_vows:
        display.info(f"  Vows fulfilled:      {fulfilled_vows}")
    display.info(f"  Active vows:         {active_vows}")
    display.info(
        f"  Momentum:            {state.character.momentum:+d}/{state.character.momentum_max}"
    )
    display.console.print()

    # Save character state
    save_path = save_game(
        character=state.character,
        vows=state.vows,
        session_count=state.session_count,
        dice_mode=state.dice_mode,
    )
    display.success(f"Character saved → {save_path}")

    # Export session markdown
    session_path = export_session(state.session, state.character)
    display.success(f"Session exported → {session_path}")

    # Append to full journal
    journal_path = append_to_journal(state.session, state.character)
    display.success(f"Journal updated → {journal_path}")

    display.console.print()
    display.info(f"  Until next time, {state.character.name}.")
    display.console.print()

    state.running = False


def handle_help(state: GameState, args: list[str], flags: set[str]) -> None:
    from soloquest.commands.registry import COMMAND_HELP

    if not args:
        display.rule("Help")
        for cmd, desc in COMMAND_HELP.items():
            display.console.print(
                f"  [bold]{cmd:<12}[/bold] {desc.split('—')[1].strip() if '—' in desc else desc}"
            )
        display.console.print()
        display.info("  Anything else you type is added to your journal.")
        display.console.print()
        return

    topic = args[0].lower()

    if topic == "moves":
        display.rule("Available Moves")
        categories: dict[str, list[str]] = {}
        for _key, move in state.moves.items():
            cat = move.get("category", "other")
            categories.setdefault(cat, []).append(move["name"])
        for cat, names in categories.items():
            display.console.print(f"  [bold]{cat.capitalize()}[/bold]")
            for name in names:
                display.console.print(f"    {name}")
        display.console.print()

    elif topic == "oracles":
        display.rule("Available Oracles")
        for key, table in state.oracles.items():
            display.console.print(f"  [bold]{table.name}[/bold]  [dim]/oracle {key}[/dim]")
        display.console.print()

    else:
        # Show a specific command help
        if topic in COMMAND_HELP:
            display.info(COMMAND_HELP[topic])
        else:
            display.error(f"Unknown help topic '{topic}'. Try: help, help moves, help oracles")
