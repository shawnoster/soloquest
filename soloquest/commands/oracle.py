"""Oracle command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from soloquest.engine.dice import roll_oracle
from soloquest.engine.oracles import OracleResult, fuzzy_match_oracle
from soloquest.sync.models import Event
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


_ORACLE_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Core", ["action", "theme", "descriptor", "focus"]),
    (
        "Characters",
        [
            "given_name",
            "family_name",
            "callsign",
            "role",
            "goal",
            "quirks",
            "disposition",
            "backstory_prompts",
            "identity",
        ],
    ),
    ("NPCs", ["npc_role", "npc_disposition", "encountered_behavior", "initial_contact"]),
    ("Places", ["location", "settlement", "settlement_name", "environment"]),
    (
        "Space",
        ["space", "deep_space", "expanse", "terminus", "outlands", "planetside", "stellar_object"],
    ),
    ("Planets", ["planet_class", "first_look", "inner_first_look", "outer_first_look", "orbital"]),
    ("Starships", ["starship", "starship_history", "starship_quirks", "fleet", "class"]),
    (
        "Factions",
        [
            "affiliation",
            "authority",
            "dominion",
            "fringe_group",
            "guild",
            "influence",
            "leadership",
            "legacy",
            "projects",
            "rumors",
            "trouble",
        ],
    ),
    (
        "Events",
        [
            "begin_a_session",
            "inciting_incident",
            "combat_action",
            "combat_event",
            "peril",
            "opportunity",
            "story_clue",
            "story_complication",
            "make_a_discovery",
            "confront_chaos",
            "sector_trouble",
        ],
    ),
    ("Yes / No", ["almost_certain", "likely", "fifty_fifty", "unlikely", "small_chance"]),
]

_ORACLE_INSPIRATIONS: list[tuple[str, str]] = [
    ("Start a new session", "/oracle begin_a_session"),
    ("Quick spark of inspiration", "/oracle action theme"),
    ("Describe a location", "/oracle descriptor location"),
    ("Create an NPC", "/oracle given_name role goal disposition quirks"),
    ("Name a settlement", "/oracle settlement_name settlement"),
    ("Meet trouble", "/oracle inciting_incident"),
    ("Discover something unexpected", "/oracle make_a_discovery"),
]


def _show_oracle_list(state: GameState) -> None:
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    # Build the grouped oracle table
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", no_wrap=True)  # category
    grid.add_column(style="dim")  # keys

    for category, keys in _ORACLE_CATEGORIES:
        # Only show keys that actually exist in the loaded tables
        available = [k for k in keys if k in state.oracles]
        if available:
            grid.add_row(category, "  ".join(available))

    # Build inspiration examples
    examples = Text("\nInspiration combos:\n", style="bold")
    for label, cmd in _ORACLE_INSPIRATIONS:
        examples.append(f"  {label:<32}", style="dim")
        examples.append(f"{cmd}\n", style="cyan")

    display.console.print(
        Panel(
            Group(grid, examples),
            title="[bold]Oracle Tables[/bold]",
            subtitle="[dim]/oracle [table] [table...][/dim]",
            border_style="cyan",
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
        display.console.print(f"  [bright_cyan]│[/bright_cyan]  [dim italic]{note}[/dim italic]")
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
    state.sync.publish(
        Event(
            player=player,
            type="oracle_roll",
            data={
                "tables": [r.table_name for r in results],
                "rolls": [r.roll for r in results],
                "results": [r.result for r in results],
                **({"note": note} if note else {}),
            },
        )
    )
