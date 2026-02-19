"""Oracle command handler."""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from rich.markup import escape

from soloquest.engine.dice import roll_oracle
from soloquest.engine.oracles import OracleResult, fuzzy_match_oracle, load_oracle_display
from soloquest.sync.models import Event
from soloquest.ui import display
from soloquest.ui.theme import BORDER_ORACLE, ORACLE_GUTTER

if TYPE_CHECKING:
    from soloquest.loop import GameState


_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@cache
def _get_oracle_display() -> tuple[list, list]:
    """Lazy-load and cache oracle display config."""
    return load_oracle_display(_DATA_DIR)


def _show_oracle_list(state: GameState) -> None:
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    _ORACLE_CATEGORIES, _ORACLE_INSPIRATIONS = _get_oracle_display()

    # Build the grouped oracle table
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", no_wrap=True)  # category
    grid.add_column(style="dim")  # keys

    for cat in _ORACLE_CATEGORIES:
        # Only show keys that actually exist in the loaded tables
        available = [k for k in cat.keys if k in state.oracles]
        if available:
            grid.add_row(cat.name, "  ".join(available))

    # Build inspiration examples
    examples = Text("\nInspiration combos:\n", style="bold")
    for insp in _ORACLE_INSPIRATIONS:
        examples.append(f"  {insp.label:<32}", style="dim")
        examples.append(f"{insp.cmd}\n", style="cyan")

    display.console.print(
        Panel(
            Group(grid, examples),
            title="[bold]Oracle Tables[/bold]",
            subtitle="[dim]/oracle [[table]] [[table...]][/dim]",
            border_style=BORDER_ORACLE,
        )
    )


def handle_oracle(state: GameState, args: list[str], flags: set[str]) -> None:
    if not args:
        _show_oracle_list(state)
        return

    if "table" in flags:
        for query in args:
            matches = fuzzy_match_oracle(query, state.oracles)
            if not matches:
                display.warn(f"Oracle table not found: '{query}'")
                continue
            display.oracle_table_view(matches[0])
        return

    # Support multiple table names followed by an optional trailing note.
    # Once we see an unmatched arg after at least one table has resolved, the
    # remaining args are treated as the note (e.g. /oracle action theme why did he lie?)
    results: list[OracleResult] = []
    note_parts: list[str] = []
    note_started = False

    for query in args:
        if note_started:
            note_parts.append(query)
            continue

        matches = fuzzy_match_oracle(query, state.oracles)
        if not matches:
            if results:
                # First unmatched word after at least one table result → start of note
                note_started = True
                note_parts.append(query)
            else:
                display.warn(f"Oracle table not found: '{query}'")
            continue

        if len(matches) > 1:
            names = ", ".join(m.name for m in matches)
            display.warn(f"Multiple matches for '{query}': {names}")
            # Use the first one anyway
            matches = matches[:1]

        table = matches[0]
        roll = roll_oracle(state.dice)
        if roll is None:
            display.info("  Oracle roll cancelled.")
            return
        result_text = table.lookup(roll)
        results.append(OracleResult(table_name=table.name, roll=roll, result=result_text))

    note = " ".join(note_parts)

    if note:
        display.console.print(
            f"  [{ORACLE_GUTTER}]│[/{ORACLE_GUTTER}]  [dim italic]{escape(note)}[/dim italic]"
        )
        state.session.add_note(note, player=state.character.name)

    # Display all results in a single panel if multiple tables
    if len(results) == 1:
        r = results[0]
        display.oracle_result_panel(r.table_name, r.roll, r.result)
    elif len(results) > 1:
        display.oracle_result_panel_combined(results)

    if not results:
        return

    player = state.character.name

    # Log each result to the session (with player attribution)
    for r in results:
        state.session.add_oracle(
            f"Oracle [{r.table_name}] roll {r.roll} → {r.result}",
            player=player,
        )

    # Publish to the sync layer (no-op for LocalAdapter, written to JSONL for FileLogAdapter)
    oracle_event = Event(
        player=player,
        type="oracle_roll",
        data={
            "tables": [r.table_name for r in results],
            "rolls": [r.roll for r in results],
            "results": [r.result for r in results],
            **({"note": note} if note else {}),
        },
    )
    state.sync.publish(oracle_event)
    state.last_oracle_event_id = oracle_event.id
