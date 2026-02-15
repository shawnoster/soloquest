"""Main game loop — GameState container and REPL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from soloquest.commands.character import (
    handle_char,
    handle_momentum,
    handle_settings,
    handle_track,
)
from soloquest.commands.completion import CommandCompleter
from soloquest.commands.debility import handle_debility
from soloquest.commands.move import handle_move
from soloquest.commands.oracle import handle_oracle
from soloquest.commands.registry import COMMAND_HELP, parse_command
from soloquest.commands.roll import handle_roll
from soloquest.commands.session import handle_end, handle_help, handle_log, handle_note
from soloquest.commands.vow import handle_fulfill, handle_progress, handle_vow
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

    # Show context when resuming (not first session)
    if session_count > 1:
        display.console.print()
        display.rule("Continuing Your Journey")

        # Show active vows
        active_vows = [v for v in vows if not v.fulfilled]
        if active_vows:
            display.console.print("  [bold]Active Vows:[/bold]")
            for vow in active_vows[:3]:  # Show up to 3 vows
                boxes = "█" * vow.boxes_filled + "░" * (10 - vow.boxes_filled)
                display.console.print(
                    f"    [dim]• {vow.description} [{vow.rank}] {boxes}[/dim]"
                )
        else:
            display.console.print("  [dim]No active vows[/dim]")

        display.rule()

    display.console.print()

    history = InMemoryHistory()
    completer = CommandCompleter()
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
                case "roll":
                    handle_roll(state, cmd.args, cmd.flags)
                case "forsake":
                    from soloquest.commands.move import _handle_forsake_vow

                    _handle_forsake_vow(state)
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
