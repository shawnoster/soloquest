"""Main game loop — GameState container and REPL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from soloquest.commands.asset import handle_asset
from soloquest.commands.character import (
    handle_char,
    handle_momentum,
    handle_settings,
    handle_track,
)
from soloquest.commands.completion import CommandCompleter
from soloquest.commands.debility import handle_debility
from soloquest.commands.guide import handle_guide
from soloquest.commands.move import handle_move
from soloquest.commands.oracle import handle_oracle
from soloquest.commands.registry import COMMAND_HELP, parse_command
from soloquest.commands.roll import handle_roll
from soloquest.commands.session import (
    handle_end,
    handle_help,
    handle_log,
    handle_newsession,
    handle_note,
)
from soloquest.commands.vow import handle_fulfill, handle_progress, handle_vow
from soloquest.engine.assets import load_assets
from soloquest.engine.dice import (
    DiceMode,
    DigitalDice,
    MixedDice,
    PhysicalDice,
    make_dice_provider,
)
from soloquest.engine.oracles import OracleTable, load_oracles
from soloquest.models.character import Character
from soloquest.models.session import Session
from soloquest.models.vow import Vow
from soloquest.state.save import autosave
from soloquest.ui import display

DATA_DIR = Path(__file__).parent / "data"

# Commands that trigger an autosave after execution
AUTOSAVE_AFTER = {
    "move",
    "oracle",
    "vow",
    "progress",
    "fulfill",
    "health",
    "spirit",
    "supply",
    "momentum",
    "debility",
    "forsake",
}


@dataclass
class GameState:
    character: Character
    vows: list[Vow]
    session: Session
    session_count: int
    dice_mode: DiceMode
    dice: DigitalDice | PhysicalDice | MixedDice
    moves: dict  # raw TOML move data
    oracles: dict[str, OracleTable]
    assets: dict  # asset definitions from dataforged
    running: bool = True
    last_result: object = field(default=None, repr=False)
    _unsaved_entries: int = field(default=0, repr=False)


def load_dataforged_moves() -> dict:
    """Load moves from dataforged JSON files."""
    import json

    path = DATA_DIR / "dataforged" / "moves.json"
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    moves: dict[str, dict] = {}

    # Recursively extract moves from nested structure
    def extract_moves(item: dict | list) -> None:
        if isinstance(item, list):
            for sub_item in item:
                extract_moves(sub_item)
        elif isinstance(item, dict) and "Moves" in item:
            # If this has "Moves" key, iterate them
            for move in item["Moves"]:
                if "$id" in move and "Name" in move:
                    # Create simplified key
                    move_id = move["$id"]
                    key_parts = move_id.split("/")
                    key = key_parts[-1].lower().replace(" ", "_").replace("-", "_")

                    # Convert dataforged format to our dict format
                    move_dict = {
                        "name": move.get("Name", key),
                        "category": key_parts[-2].lower() if len(key_parts) > 1 else "general",
                        "description": move.get("Text", ""),
                    }

                    # Note: Dataforged doesn't include stat_options or outcome text
                    # We'll rely on TOML for detailed move mechanics
                    # This just provides the basic move definitions
                    moves[key] = move_dict

    extract_moves(data)
    return moves


def load_move_data() -> dict:
    """Load all move data from both TOML and dataforged JSON.

    TOML takes priority to allow custom overrides with full mechanics.
    """
    import tomllib

    # Start with dataforged (basic definitions)
    moves = load_dataforged_moves()

    # Load and overlay TOML (full mechanics and custom)
    toml_path = DATA_DIR / "moves.toml"
    if toml_path.exists():
        with toml_path.open("rb") as f:
            toml_moves = tomllib.load(f)
        moves.update(toml_moves)

    return moves


def run_session(
    character: Character,
    vows: list[Vow],
    session_count: int,
    dice_mode: DiceMode,
    session: Session | None = None,
) -> None:
    # If no session provided, create a new one
    if session is None:
        session_count += 1
        session = Session(number=session_count)
    else:
        # Resume existing session (session_count remains the same)
        pass

    moves = load_move_data()
    oracles = load_oracles(DATA_DIR)
    assets = load_assets(DATA_DIR)
    dice = make_dice_provider(dice_mode)

    state = GameState(
        character=character,
        vows=vows,
        session=session,
        session_count=session_count,
        dice_mode=dice_mode,
        dice=dice,
        moves=moves,
        oracles=oracles,
        assets=assets,
    )

    is_new_session = session.number == session_count and len(session.entries) == 0
    resume_label = "" if is_new_session else " (Resumed)"
    display.session_header(session.number, resume_label)
    display.info(f"  Character: {character.name}  |  Dice: {dice_mode.value}")
    display.info("  Type to journal. /guide for gameplay loop, /help for commands.")

    # Show context when resuming (not first session)
    if session.number > 1 and is_new_session:
        display.console.print()
        display.rule("Continuing Your Journey")

        # Show active vows
        active_vows = [v for v in vows if not v.fulfilled]
        if active_vows:
            display.console.print("  [bold]Active Vows:[/bold]")
            for vow in active_vows[:3]:  # Show up to 3 vows
                boxes = "█" * vow.boxes_filled + "░" * (10 - vow.boxes_filled)
                display.console.print(f"    [dim]• {vow.description} [{vow.rank}] {boxes}[/dim]")
        else:
            display.console.print("  [dim]No active vows[/dim]")

        display.rule()

    display.console.print()

    history = InMemoryHistory()
    completer = CommandCompleter(oracles=state.oracles, moves=state.moves, assets=state.assets)
    prompt_session: PromptSession = PromptSession(
        history=history,
        completer=completer,
        complete_while_typing=False,  # Only complete on Tab
    )

    while state.running:
        try:
            line = prompt_session.prompt("> ")
        except (KeyboardInterrupt, EOFError):
            display.console.print()
            _handle_interrupt(state)
            break

        line = line.strip()
        if not line:
            continue

        cmd = parse_command(line)

        if cmd is None:
            # Plain text → journal entry
            state.session.add_journal(line)
            state._unsaved_entries += 1
            continue

        # Dispatch with error handling
        try:
            match cmd.name:
                case "guide":
                    handle_guide(state, cmd.args, cmd.flags)
                case "move":
                    handle_move(state, cmd.args, cmd.flags)
                case "oracle":
                    handle_oracle(state, cmd.args, cmd.flags)
                case "asset":
                    handle_asset(state, cmd.args, cmd.flags)
                case "vow":
                    handle_vow(state, cmd.args, cmd.flags)
                case "progress":
                    handle_progress(state, cmd.args, cmd.flags)
                case "fulfill":
                    handle_fulfill(state, cmd.args, cmd.flags)
                case "char":
                    handle_char(state, cmd.args, cmd.flags)
                case "log":
                    handle_log(state, cmd.args, cmd.flags)
                case "note":
                    handle_note(state, cmd.args, cmd.flags)
                case "health" | "spirit" | "supply":
                    handle_track(state, cmd.name, cmd.args)
                case "momentum":
                    handle_momentum(state, cmd.args, cmd.flags)
                case "debility":
                    handle_debility(state, cmd.args, cmd.flags)
                case "roll":
                    handle_roll(state, cmd.args, cmd.flags)
                case "forsake":
                    from soloquest.commands.move import _handle_forsake_vow

                    _handle_forsake_vow(state)
                case "settings":
                    handle_settings(state, cmd.args, cmd.flags)
                case "newsession":
                    handle_newsession(state, cmd.args, cmd.flags)
                case "end":
                    handle_end(state, cmd.args, cmd.flags)
                case "help":
                    handle_help(state, cmd.args, cmd.flags)
                case "quit" | "q":
                    _confirm_quit(state)
                case _:
                    known = list(COMMAND_HELP.keys())
                    close = [k for k in known if k.startswith(cmd.name)]
                    if close:
                        display.warn(
                            f"Unknown command '/{cmd.name}'. Did you mean: "
                            + ", ".join(f"/{c}" for c in close)
                            + "?"
                        )
                    else:
                        display.error(f"Unknown command '/{cmd.name}'. Type /help for commands.")
                    continue  # skip autosave on unknown commands

            # Autosave after mechanical commands
            if cmd.name in AUTOSAVE_AFTER:
                autosave(
                    state.character, state.vows, state.session_count, state.dice_mode, state.session
                )
                state._unsaved_entries = 0

        except ValueError as e:
            display.error(f"Invalid value: {e}")
            display.info("  Type /help for usage information.")
        except KeyError as e:
            display.error(f"Missing data: {e}")
            display.warn("  Your save file may be corrupted.")
        except AttributeError as e:
            display.error(f"Invalid attribute: {e}")
            display.info("  This is a bug. Please report it.")
        except Exception as e:
            display.error(f"Unexpected error: {e}")
            display.warn("  Game state preserved. Continue playing.")


def _handle_interrupt(state: GameState) -> None:
    """Ctrl+C handler — autosave session and character state."""
    # Always autosave the current session
    autosave(state.character, state.vows, state.session_count, state.dice_mode, state.session)
    display.info(
        "Session saved. Resume with 'soloquest' or start a new session with '/newsession'."
    )


def _confirm_quit(state: GameState) -> None:
    """Quit and autosave session."""
    # Always autosave the current session
    autosave(state.character, state.vows, state.session_count, state.dice_mode, state.session)
    display.info(
        "Session saved. Resume with 'soloquest' or start a new session with '/newsession'."
    )
    state.running = False
