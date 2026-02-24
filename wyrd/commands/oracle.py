"""Oracle command handler."""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from rich.markup import escape

from wyrd.engine.dice import roll_oracle
from wyrd.engine.oracles import OracleResult, fuzzy_match_oracle, load_oracle_display
from wyrd.sync.models import Event
from wyrd.ui import display
from wyrd.ui.strings import get_string
from wyrd.ui.theme import BORDER_ORACLE, ORACLE_GUTTER

if TYPE_CHECKING:
    from wyrd.loop import GameState


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
    examples = Text(get_string("oracle.inspiration_header"), style="bold")
    for insp in _ORACLE_INSPIRATIONS:
        examples.append(f"  {insp.label:<32}", style="dim")
        examples.append(f"{insp.cmd}\n", style="cyan")

    display.console.print(
        Panel(
            Group(grid, examples),
            title=get_string("oracle.panel_title"),
            subtitle=get_string("oracle.panel_subtitle"),
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
                display.warn(get_string("oracle.not_found", query=query))
                continue
            display.oracle_table_view(matches[0])
        return

    # Two-pass parsing:
    # Pass 1: greedily match table names from the front; collect trailing args.
    # If the only trailing arg is a bare integer, use it as a direct lookup
    # (e.g. /oracle action 23 → show row 23, no dice roll).
    # Otherwise trailing args become a note with a normal random roll
    # (e.g. /oracle action and then there were 23 ghosts).
    table_queries = []
    trailing: list[str] = []

    for query in args:
        if trailing:
            trailing.append(query)
            continue
        matches = fuzzy_match_oracle(query, state.oracles)
        if matches:
            if len(matches) > 1:
                names = ", ".join(m.name for m in matches)
                display.warn(get_string("oracle.multiple_matches", query=query, names=names))
                matches = matches[:1]
            table_queries.append(matches[0])
        else:
            if table_queries:
                trailing.append(query)
            else:
                display.warn(get_string("oracle.not_found", query=query))

    if not table_queries:
        return

    direct_roll: int | None = None
    note_parts: list[str] = []

    if len(trailing) == 1 and trailing[0].isdigit():
        direct_roll = int(trailing[0])
    else:
        note_parts = trailing

    # Pass 2: roll (or direct-lookup) each matched table
    results: list[OracleResult] = []

    for table in table_queries:
        if direct_roll is not None:
            roll = direct_roll
        else:
            roll = roll_oracle(state.dice)
            if roll is None:
                display.info(get_string("oracle.cancelled"))
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
        log_text = get_string("oracle.log_format", table=r.table_name, roll=r.roll, result=r.result)
        state.session.add_oracle(log_text, player=player)

    # Publish to the sync layer (no-op for LocalAdapter, written to JSONL for FileLogAdapter)
    oracle_event = Event(
        player=player,
        type="oracle_roll",  # Machine-readable identifier - must remain constant
        data={
            "tables": [r.table_name for r in results],
            "rolls": [r.roll for r in results],
            "results": [r.result for r in results],
            **({"note": note} if note else {}),
        },
    )
    state.sync.publish(oracle_event)
    state.last_oracle_event_id = oracle_event.id
