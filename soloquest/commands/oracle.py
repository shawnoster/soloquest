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

    # Support multiple table names in one command (e.g. /oracle action theme)
    # Try each arg as a table lookup, accumulate results
    results: list[OracleResult] = []

    for query in args:
        matches = fuzzy_match_oracle(query, state.oracles)
        if not matches:
            display.warn(f"Oracle table not found: '{query}'")
            continue
        if len(matches) > 1:
            names = ", ".join(m.name for m in matches)
            display.warn(f"Multiple matches for '{query}': {names}")
            # Use the first one anyway
            matches = matches[:1]

        table = matches[0]
        roll = roll_oracle(state.dice)
        result_text = table.lookup(roll)
        results.append(OracleResult(table_name=table.name, roll=roll, result=result_text))

    for r in results:
        display.oracle_result_panel(r.table_name, r.roll, r.result)
        log_text = f"Oracle [{r.table_name}] roll {r.roll} → {r.result}"
        state.session.add_oracle(log_text)
