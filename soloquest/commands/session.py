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


def handle_edit(state: GameState, args: list[str], flags: set[str]) -> None:
    """Open external editor to write a journal entry."""
    import os
    import subprocess
    import tempfile

    # Check for EDITOR environment variable
    editor = os.environ.get("EDITOR")
    if not editor:
        display.error("No editor configured. Set $EDITOR environment variable.")
        display.info("  Example: export EDITOR=vim")
        return

    # Create temporary file for editing
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as tmp_file:
        tmp_path = tmp_file.name
        # Add helpful instruction at top
        tmp_file.write("# Write your journal entry below (lines starting with # will be ignored)\n\n")

    try:
        # Open editor
        display.info(f"Opening {editor}...")
        result = subprocess.run([editor, tmp_path], check=False)

        if result.returncode != 0:
            display.error(f"Editor exited with error code {result.returncode}")
            return

        # Read content from file
        with open(tmp_path, encoding="utf-8") as f:
            content = f.read()

        # Remove comment lines and strip whitespace
        lines = [line for line in content.split("\n") if not line.strip().startswith("#")]
        text = "\n".join(lines).strip()

        if not text:
            display.warn("No content written. Journal entry cancelled.")
            return

        # Add to session journal
        state.session.add_journal(text)
        state._unsaved_entries += 1

        # Show preview of what was added
        preview = text[:100] + "..." if len(text) > 100 else text
        display.success(f"Journal entry added: {preview}")

    finally:
        # Clean up temp file
        from contextlib import suppress

        with suppress(OSError):
            os.unlink(tmp_path)


def handle_newsession(state: GameState, args: list[str], flags: set[str]) -> None:
    """Start a new session — export current session journal, then start fresh."""
    from rich.prompt import Confirm

    if len(state.session.entries) > 0:
        display.rule("Start New Session")
        display.warn("This will export the current session and start fresh.")
        display.info(f"  Current session has {len(state.session.entries)} entries.")
        display.console.print()

        if not Confirm.ask("  Start new session?", default=False):
            return

        # Export current session first
        _export_session(state)

    # Create new session
    state.session_count += 1
    from soloquest.models.session import Session

    state.session = Session(number=state.session_count)

    # Save character state with new session
    from soloquest.state.save import save_game

    save_path = save_game(
        character=state.character,
        vows=state.vows,
        session_count=state.session_count,
        dice_mode=state.dice_mode,
        session=state.session,
    )
    display.success(f"Character saved → {save_path}")
    display.console.print()
    display.session_header(state.session.number, "")
    display.info(f"  Character: {state.character.name}  |  Dice: {state.dice_mode.value}")
    display.console.print()


def _export_session(state: GameState) -> None:
    """Export current session to markdown files."""
    # Session markdown
    session_path = export_session(state.session, state.character)
    display.success(f"Session exported → {session_path}")

    # Append to full journal
    journal_path = append_to_journal(state.session, state.character)
    display.success(f"Journal updated → {journal_path}")


def handle_end(state: GameState, args: list[str], flags: set[str]) -> None:
    """Export current session journal and exit."""
    display.rule("End Session")

    has_entries = len(state.session.entries) > 0

    if has_entries:
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

        # Export session journal
        _export_session(state)
    else:
        display.info("  Session has no entries to export.")
        display.console.print()

    # Always save character state (even if no entries)
    save_path = save_game(
        character=state.character,
        vows=state.vows,
        session_count=state.session_count,
        dice_mode=state.dice_mode,
        session=None,  # Clear session after export
    )
    display.success(f"Character saved → {save_path}")

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
