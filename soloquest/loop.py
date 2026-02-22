"""Main game loop — GameState container and REPL."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from soloquest.commands.asset import handle_asset
from soloquest.commands.campaign import handle_campaign
from soloquest.commands.character import (
    handle_char,
    handle_momentum,
    handle_settings,
    handle_track,
)
from soloquest.commands.completion import CommandCompleter
from soloquest.commands.debility import handle_debility
from soloquest.commands.guide import handle_guide
from soloquest.commands.guided_mode import advance_phase, stop_guided_mode
from soloquest.commands.interpret import handle_accept, handle_interpret
from soloquest.commands.move import handle_move
from soloquest.commands.oracle import handle_oracle
from soloquest.commands.registry import COMMAND_HELP, parse_command
from soloquest.commands.roll import handle_roll
from soloquest.commands.session import (
    handle_edit,
    handle_end,
    handle_help,
    handle_log,
    handle_newsession,
    handle_note,
)
from soloquest.commands.truths import handle_truths
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
from soloquest.engine.truths import TruthCategory, load_truth_categories
from soloquest.models.campaign import CampaignState
from soloquest.models.character import Character
from soloquest.models.session import Session
from soloquest.models.vow import Vow
from soloquest.state.save import autosave
from soloquest.sync import FileLogAdapter, LocalAdapter, SyncPort
from soloquest.ui import display
from soloquest.ui.strings import get_string

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
    "truths",
    "asset",
    "campaign",
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
    truth_categories: dict[str, TruthCategory]  # truth categories for campaign setup
    running: bool = True
    last_result: object = field(default=None, repr=False)
    _unsaved_entries: int = field(default=0, repr=False)
    guided_mode: bool = field(default=False, repr=False)
    guided_phase: str = field(default="envision", repr=False)  # envision, oracle, move, outcome
    sync: SyncPort = field(default_factory=lambda: LocalAdapter("solo"), repr=False)
    campaign: CampaignState | None = field(default=None, repr=False)
    campaign_dir: Path | None = field(default=None, repr=False)
    last_oracle_event_id: str | None = field(default=None, repr=False)
    pending_partner_interpretation: object = field(default=None, repr=False)  # Event | None
    last_proposed_truth_category: str | None = field(default=None, repr=False)


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


def _get_multiline_journal_entry(prompt_session: PromptSession, first_line: str) -> str | None:
    """Capture multi-line journal entry using paragraph blocks.
    
    - Press Enter twice to add a new paragraph
    - Single Enter adds line break within paragraph
    - Ctrl+D to finish and submit
    - Ctrl+C to cancel
    
    Args:
        prompt_session: The prompt session to use
        first_line: The first line already entered
        
    Returns:
        The complete journal entry, or None if cancelled
    """
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.key_binding import KeyBindings
    
    # Sentinel value to mark paragraph breaks
    PARAGRAPH_BREAK = "<<<PARAGRAPH_BREAK>>>"
    
    lines = [first_line]
    display.info("Multi-line mode: Press Enter twice for paragraph, Ctrl+D to finish, Ctrl+C to cancel")
    
    # Create custom key bindings for multi-line input
    bindings = KeyBindings()
    
    @bindings.add('c-d')
    def _(event):
        """Accept input on Ctrl+D."""
        event.current_buffer.validate_and_handle()
    
    while True:
        try:
            # Prompt for next line with continuation indicator
            line = prompt_session.prompt(
                HTML("<ansibrightblue>▌</ansibrightblue> "),
                key_bindings=bindings,
                multiline=False,  # We handle multi-line logic ourselves
            )
            
            line = line.strip()
            
            # Empty line means paragraph break or continuation
            if not line:
                # Check if previous line was also empty (double enter)
                if lines and lines[-1] == "":
                    # Remove the previous empty line and add paragraph break marker
                    lines.pop()
                    lines.append(PARAGRAPH_BREAK)
                else:
                    # First empty line - could be paragraph break
                    lines.append("")
            else:
                lines.append(line)
                
        except EOFError:
            # Ctrl+D pressed - finish entry
            # Clean up trailing empty lines (but preserve paragraph breaks)
            while lines and lines[-1] == "":
                lines.pop()
            
            if not lines:
                return None
                
            # Convert paragraph break markers to double newlines
            result = []
            for line in lines:
                if line == PARAGRAPH_BREAK:
                    # Add paragraph break (double newline = empty line between paragraphs)
                    result.append("")
                else:
                    result.append(line)
            
            return "\n".join(result)
            
        except KeyboardInterrupt:
            # Ctrl+C pressed - cancel
            display.info("Journal entry cancelled")
            return None


def run_session(
    character: Character,
    vows: list[Vow],
    session_count: int,
    dice_mode: DiceMode,
    session: Session | None = None,
    campaign=None,
    campaign_dir: Path | None = None,
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
    truth_categories = load_truth_categories(DATA_DIR)
    dice = make_dice_provider(dice_mode)

    sync: SyncPort = (
        FileLogAdapter(campaign_dir, character.name)
        if campaign_dir
        else LocalAdapter(character.name)
    )

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
        truth_categories=truth_categories,
        sync=sync,
        campaign=campaign,
        campaign_dir=campaign_dir,
    )

    is_new_session = session.number == session_count and len(session.entries) == 0
    resume_label = "" if is_new_session else " (Resumed)"
    display.session_header(session.number, resume_label)
    display.info(get_string("session_header.help_text"))

    # Show context when resuming (not first session)
    if session.number > 1 and is_new_session:
        display.console.print()
        display.rule(get_string("session_header.continuing_journey"))

        # Show active vows
        active_vows = [v for v in vows if not v.fulfilled]
        if active_vows:
            display.console.print(get_string("session_header.active_vows_label"))
            for vow in active_vows[:3]:  # Show up to 3 vows
                boxes = "█" * vow.boxes_filled + "░" * (10 - vow.boxes_filled)
                display.console.print(f"    [dim]• {vow.description} [{vow.rank}] {boxes}[/dim]")
        else:
            display.console.print(get_string("session_header.no_active_vows"))

        display.rule()

    display.console.print()

    # Use FileHistory for persistent command history across sessions
    from soloquest.config import config

    history_path = config.adventures_dir / ".soloquest_history"
    config.adventures_dir.mkdir(parents=True, exist_ok=True)
    history = FileHistory(str(history_path))
    completer = CommandCompleter(oracles=state.oracles, moves=state.moves, assets=state.assets)
    prompt_session: PromptSession = PromptSession(
        history=history,
        completer=completer,
        complete_while_typing=False,  # Only complete on Tab
    )

    while state.running:
        try:
            # Use guided prompt if in guided mode
            if state.guided_mode:
                from soloquest.commands.guided_mode import get_guided_prompt_html

                prompt_text = get_guided_prompt_html(state)
                line = prompt_session.prompt(prompt_text)
            else:
                from prompt_toolkit.formatted_text import HTML

                line = prompt_session.prompt(
                    HTML("<ansibrightblue>▌</ansibrightblue>\n<ansibrightblue>▌</ansibrightblue> ")
                )
        except (KeyboardInterrupt, EOFError):
            display.console.print()
            _handle_interrupt(state)
            break

        line = line.strip()
        if not line:
            continue

        cmd = parse_command(line)

        if cmd is None:
            # Plain text → potential journal entry
            # Enter multi-line mode to allow paragraph blocks
            full_entry = _get_multiline_journal_entry(prompt_session, line)
            if full_entry is not None:
                state.session.add_journal(full_entry)
                state._unsaved_entries += 1
            continue

        # Dispatch with error handling
        try:
            match cmd.name:
                case "next":
                    advance_phase(state)
                case "guide":
                    handle_guide(state, cmd.args, cmd.flags)
                case "campaign":
                    handle_campaign(state, cmd.args, cmd.flags)
                case "truths":
                    handle_truths(state, cmd.args, cmd.flags)
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
                case "edit":
                    handle_edit(state, cmd.args, cmd.flags)
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
                case "clear":
                    display.console.clear()
                case "help":
                    handle_help(state, cmd.args, cmd.flags)
                case "interpret":
                    handle_interpret(state, cmd.args, cmd.flags)
                case "accept":
                    handle_accept(state, cmd.args, cmd.flags)
                case "sync":
                    _poll_and_display(state, explicit=True)
                    continue  # no autosave needed
                case "quit" | "q" | "exit":
                    if state.guided_mode:
                        stop_guided_mode(state)
                    else:
                        _confirm_quit(state)
                case _:
                    known = list(COMMAND_HELP.keys())
                    close = [k for k in known if k.startswith(cmd.name)]
                    if close:
                        suggestions = ", ".join(f"/{c}" for c in close)
                        display.warn(get_string("loop.did_you_mean", cmd=cmd.name, suggestions=suggestions))
                    else:
                        display.error(get_string("loop.unknown_command", cmd=cmd.name))
                    continue  # skip autosave on unknown commands

            # Autosave after mechanical commands
            if cmd.name in AUTOSAVE_AFTER:
                _autosave_state(state)
                state._unsaved_entries = 0

            # Poll for partner activity after each command (co-op only)
            _poll_and_display(state)

        except ValueError as e:
            display.error(get_string("loop.invalid_value", error=e))
            display.info(get_string("loop.help_info"))
        except KeyError as e:
            display.error(get_string("loop.missing_data", error=e))
            display.warn(get_string("loop.corrupted_save_warn"))
        except AttributeError as e:
            display.error(get_string("loop.invalid_attribute", error=e))
            display.info(get_string("loop.bug_report"))
        except Exception as e:
            display.error(get_string("loop.unexpected_error", error=e))
            display.warn(get_string("loop.state_preserved"))


def _poll_and_display(state: GameState, explicit: bool = False) -> None:
    """Poll for partner events and display any that arrive.

    Only active in co-op mode (campaign is not None). In solo mode this is
    a no-op because LocalAdapter.poll() always returns [].

    Args:
        explicit: True when called from /sync command — show a message even
                  if there are no new events.
    """
    if state.campaign is None and not explicit:
        return
    events = state.sync.poll()
    if events:
        display.partner_activity(events)
        # Track relevant partner events for follow-up commands
        for event in events:
            if event.type == "interpret":
                state.pending_partner_interpretation = event
            elif event.type == "accept_truth" and event.player != state.sync.player_id:
                # A partner accepted a truth we proposed — apply it to our character too
                _apply_accepted_truth_to_character(state, event)
    elif explicit:
        display.info(get_string("loop.no_partner_activity"))


def _apply_accepted_truth_to_character(state: GameState, event: object) -> None:
    """When a partner accepts a truth we proposed, apply it to our character."""
    from soloquest.sync.models import Event

    assert isinstance(event, Event)
    cat = event.data.get("category", "")
    summary = event.data.get("option_summary", "")
    if not cat:
        return

    # Only apply if we don't already have this truth set
    existing = [t for t in state.character.truths if t.category == cat]
    if existing:
        return

    from soloquest.models.truths import ChosenTruth

    truth = ChosenTruth(category=cat, option_summary=summary)
    state.character.truths.append(truth)


def _autosave_state(state: GameState) -> None:
    """Autosave using campaign-aware save path."""
    from soloquest.state.campaign import player_save_path

    save_path = None
    if state.campaign_dir is not None:
        save_path = player_save_path(state.campaign_dir, state.character.name)

    autosave(
        state.character,
        state.vows,
        state.session_count,
        state.dice_mode,
        state.session,
        save_path=save_path,
    )


def _handle_interrupt(state: GameState) -> None:
    """Ctrl+C handler — autosave session and character state."""
    _autosave_state(state)
    display.info(get_string("quit.session_saved"))


def _confirm_quit(state: GameState) -> None:
    """Quit and autosave session."""
    _autosave_state(state)
    display.info(get_string("quit.session_saved"))
    state.running = False
