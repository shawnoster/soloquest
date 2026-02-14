"""Main game loop — GameState container and REPL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from starforged.commands.character import (
    handle_char,
    handle_momentum,
    handle_settings,
    handle_track,
)
from starforged.commands.debility import handle_debility
from starforged.commands.move import handle_move
from starforged.commands.oracle import handle_oracle
from starforged.commands.registry import COMMAND_HELP, parse_command
from starforged.commands.session import handle_end, handle_help, handle_log, handle_note
from starforged.commands.vow import handle_fulfill, handle_progress, handle_vow
from starforged.engine.dice import (
    DiceMode,
    DigitalDice,
    MixedDice,
    PhysicalDice,
    make_dice_provider,
)
from starforged.engine.oracles import OracleTable, load_oracles
from starforged.models.character import Character
from starforged.models.session import Session
from starforged.models.vow import Vow
from starforged.state.save import autosave
from starforged.ui import display

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
    running: bool = True
    last_result: object = field(default=None, repr=False)
    _unsaved_entries: int = field(default=0, repr=False)


def load_move_data() -> dict:
    import tomllib

    path = DATA_DIR / "moves.toml"
    with path.open("rb") as f:
        return tomllib.load(f)


def run_session(
    character: Character,
    vows: list[Vow],
    session_count: int,
    dice_mode: DiceMode,
) -> None:
    session_count += 1
    session = Session(number=session_count)

    moves = load_move_data()
    oracles = load_oracles(DATA_DIR)
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
    )

    display.session_header(session_count, "")
    display.info(f"  Character: {character.name}  |  Dice: {dice_mode.value}")
    display.info("  Type to journal. /help for commands.")
    display.console.print()

    history = InMemoryHistory()
    prompt_session: PromptSession = PromptSession(history=history)

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

        # Dispatch
        match cmd.name:
            case "move":
                handle_move(state, cmd.args, cmd.flags)
            case "oracle":
                handle_oracle(state, cmd.args, cmd.flags)
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
            case "settings":
                handle_settings(state, cmd.args, cmd.flags)
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
            autosave(state.character, state.vows, state.session_count, state.dice_mode)
            state._unsaved_entries = 0


def _handle_interrupt(state: GameState) -> None:
    """Ctrl+C handler — offer to save if there are unsaved entries."""
    if state._unsaved_entries > 0:
        display.warn(
            f"Session interrupted with {state._unsaved_entries} unsaved journal "
            f"entr{'y' if state._unsaved_entries == 1 else 'ies'}. Use /end to save."
        )
    else:
        display.info("Session interrupted. Use /end to save.")


def _confirm_quit(state: GameState) -> None:
    """Quit with confirmation if there are unsaved journal entries."""
    if state._unsaved_entries > 0:
        display.warn(
            f"You have {state._unsaved_entries} unsaved journal "
            f"entr{'y' if state._unsaved_entries == 1 else 'ies'}."
        )
        from rich.prompt import Confirm

        if not Confirm.ask("  Quit without saving?", default=False):
            return
    else:
        display.info("Quitting without saving.")
    state.running = False
