"""Oracle command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from soloquest.engine.dice import roll_oracle
from soloquest.engine.oracles import OracleResult, fuzzy_match_oracle
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def handle_oracle(state: GameState, args: list[str], flags: set[str]) -> None:
    if not args:
        display.error("Usage: /oracle [table]  (e.g. /oracle action theme)")
        display.info("Try /help oracles to see available tables.")
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

    # Display all results in a single panel if multiple tables
    if len(results) == 1:
        r = results[0]
        display.oracle_result_panel(r.table_name, r.roll, r.result)
    elif len(results) > 1:
        display.oracle_result_panel_combined(results)

    if note:
        display.console.print(f"     [dim italic]{note}[/dim italic]")

    # Log each result separately
    for r in results:
        log_text = f"Oracle [{r.table_name}] roll {r.roll} → {r.result}"
        if note:
            log_text += f" — {note}"
        state.session.add_oracle(log_text)
