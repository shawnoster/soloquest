"""Campaign command — create, join, and inspect co-op campaigns."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from soloquest.commands.new_character import run_new_character_flow
from soloquest.engine.dice import make_dice_provider
from soloquest.state.campaign import (
    campaign_path,
    create_campaign,
    join_campaign,
    list_campaigns,
    load_campaign,
    player_save_path,
)
from soloquest.state.save import save_game
from soloquest.sync import FileLogAdapter, LocalAdapter
from soloquest.ui import display
from soloquest.ui.theme import BORDER_REFERENCE, COOP_TRUTH, HINT_COMMAND

if TYPE_CHECKING:
    from soloquest.loop import GameState

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def handle_campaign(state: GameState, args: list[str], flags: set[str]) -> None:
    """Manage co-op campaigns.

    Usage:
        /campaign            — show campaign status (or prompt to create/join)
        /campaign start      — begin your adventure (solo, create co-op, or join)
        /campaign create     — create a new campaign
        /campaign join       — join an existing campaign
        /campaign status     — show current campaign info and players
        /campaign leave      — leave the current campaign (returns to solo mode)
    """
    sub = args[0].lower() if args else ""

    if sub == "start":
        _handle_start(state)
    elif sub == "create":
        _handle_create(state)
    elif sub == "join":
        _handle_join(state)
    elif sub == "status":
        _handle_status(state)
    elif sub == "leave":
        _handle_leave(state)
    else:
        if state.campaign is None:
            _show_no_campaign_help()
        else:
            _handle_status(state)


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def _handle_start(state: GameState) -> None:
    """Unified adventure start wizard: solo, create co-op, or join co-op."""
    display.rule("Begin Your Adventure")
    display.console.print()
    display.console.print("  [bold]1)[/bold] Solo Adventure")
    display.console.print("  [bold]2)[/bold] Create Co-op Campaign")
    display.console.print("  [bold]3)[/bold] Join Campaign")
    display.console.print()

    choice = Prompt.ask("  Choose", choices=["1", "2", "3"], default="1")

    if choice == "1":
        _handle_start_solo(state)
    elif choice == "2":
        _handle_start_create_coop(state)
    elif choice == "3":
        _handle_start_join_coop(state)


def _handle_start_solo(state: GameState) -> None:
    """Solo adventure: truths + character creation → save."""
    result = run_new_character_flow(
        _DATA_DIR, state.truth_categories, include_truths=True, state=state
    )
    if result is None:
        display.warn("Campaign setup cancelled.")
        return

    character, vows, dice_mode, truths = result
    state.character = character
    state.vows = vows
    state.dice_mode = dice_mode
    state.dice = make_dice_provider(dice_mode)
    state.session_count = 0
    state.truths = truths

    save_game(character, vows, 0, dice_mode)
    display.success(f"Adventure begun as {character.name}!")


def _handle_start_create_coop(state: GameState) -> None:
    """Create co-op campaign: campaign name + truths + char creation → save in players/."""
    name = Prompt.ask("Campaign name")
    if not name.strip():
        display.warn("Campaign name cannot be empty.")
        return

    result = run_new_character_flow(
        _DATA_DIR, state.truth_categories, include_truths=True, state=state
    )
    if result is None:
        display.warn("Campaign setup cancelled.")
        return

    character, vows, dice_mode, truths = result

    try:
        campaign, campaign_dir = create_campaign(name.strip(), character.name)
    except ValueError as e:
        display.error(str(e))
        return

    state.character = character
    state.vows = vows
    state.dice_mode = dice_mode
    state.dice = make_dice_provider(dice_mode)
    state.session_count = 0
    state.truths = truths
    state.campaign = campaign
    state.campaign_dir = campaign_dir
    state.sync = FileLogAdapter(campaign_dir, character.name)

    save_path = player_save_path(campaign_dir, character.name)
    save_game(character, vows, 0, dice_mode, save_path=save_path)
    display.success(f"Campaign '{campaign.name}' created! You are playing as {character.name}.")
    display.info(f"  Share the campaign directory with other players: {campaign_dir}")


def _handle_start_join_coop(state: GameState) -> None:
    """Join existing campaign: pick campaign → char creation (no truths) → save in players/."""
    campaigns = list_campaigns()
    if not campaigns:
        display.warn("No campaigns found. Use option 2 to create one first.")
        return

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Slug")
    table.add_column("Players")

    for i, slug in enumerate(campaigns, 1):
        try:
            c = load_campaign(campaign_path(slug))
            players = ", ".join(c.players.keys()) or "(none)"
            table.add_row(str(i), slug, players)
        except Exception:
            table.add_row(str(i), slug, "[dim](unreadable)[/dim]")

    display.console.print(table)

    choice = Prompt.ask("Enter campaign number or slug")
    if not choice.strip():
        return

    slug: str | None = None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(campaigns):
            slug = campaigns[idx]
    else:
        slug = choice.strip() if choice.strip() in campaigns else None

    if slug is None:
        display.error(f"Campaign '{choice}' not found.")
        return

    result = run_new_character_flow(
        _DATA_DIR, state.truth_categories, include_truths=False, state=state
    )
    if result is None:
        display.warn("Character creation cancelled.")
        return

    character, vows, dice_mode, _truths = result
    target_dir = campaign_path(slug)

    try:
        campaign = join_campaign(target_dir, character.name)
    except Exception as e:
        display.error(str(e))
        return

    state.character = character
    state.vows = vows
    state.dice_mode = dice_mode
    state.dice = make_dice_provider(dice_mode)
    state.session_count = 0
    state.campaign = campaign
    state.campaign_dir = target_dir
    state.sync = FileLogAdapter(target_dir, character.name)

    save_path = player_save_path(target_dir, character.name)
    save_game(character, vows, 0, dice_mode, save_path=save_path)
    display.success(f"Joined campaign '{campaign.name}' as '{character.name}'!")


def _handle_create(state: GameState) -> None:
    """Create a new campaign and join it as the first player."""
    display.rule("Create Campaign")

    if state.campaign is not None:
        display.warn(
            f"You are already in campaign '{state.campaign.name}'. Use /campaign leave first."
        )
        return

    name = Prompt.ask("Campaign name")
    if not name.strip():
        display.warn("Campaign name cannot be empty.")
        return

    player_id = state.character.name

    try:
        campaign, campaign_dir = create_campaign(name.strip(), player_id)
    except ValueError as e:
        display.error(str(e))
        return

    # Wire up state
    state.campaign = campaign
    state.campaign_dir = campaign_dir
    state.sync = FileLogAdapter(campaign_dir, player_id)

    display.success(f"Campaign '{campaign.name}' created.")
    display.info(f"  Slug: {campaign.slug}")
    display.info(f"  Directory: {campaign_dir}")
    display.info(f"  Player: {player_id}")
    display.info("")
    display.info("  Share the campaign directory with other players so they can /campaign join.")


def _handle_join(state: GameState) -> None:
    """Join an existing campaign by selecting from known campaigns."""
    display.rule("Join Campaign")

    if state.campaign is not None:
        display.warn(
            f"You are already in campaign '{state.campaign.name}'. Use /campaign leave first."
        )
        return

    campaigns = list_campaigns()
    if not campaigns:
        display.warn("No campaigns found. Use /campaign create to start one.")
        return

    # Show available campaigns
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Slug")
    table.add_column("Players")

    for i, slug in enumerate(campaigns, 1):
        try:
            c = load_campaign(campaign_path(slug))
            players = ", ".join(c.players.keys()) or "(none)"
            table.add_row(str(i), slug, players)
        except Exception:
            table.add_row(str(i), slug, "[dim](unreadable)[/dim]")

    display.console.print(table)

    choice = Prompt.ask("Enter campaign number or slug")
    if not choice.strip():
        return

    # Resolve selection
    slug: str | None = None
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(campaigns):
            slug = campaigns[idx]
    else:
        slug = choice.strip() if choice.strip() in campaigns else None

    if slug is None:
        display.error(f"Campaign '{choice}' not found.")
        return

    player_id = state.character.name
    target_dir = campaign_path(slug)

    try:
        campaign = join_campaign(target_dir, player_id)
    except ValueError as e:
        display.error(str(e))
        return

    # Wire up state
    state.campaign = campaign
    state.campaign_dir = target_dir
    state.sync = FileLogAdapter(target_dir, player_id)

    display.success(f"Joined campaign '{campaign.name}' as '{player_id}'.")
    display.info(f"  Directory: {target_dir}")


def _handle_status(state: GameState) -> None:
    """Show current campaign info."""
    if state.campaign is None:
        _show_no_campaign_help()
        return

    display.rule(f"Campaign: {state.campaign.name}")
    display.info(f"  Slug:    {state.campaign.slug}")
    display.info(f"  Created: {state.campaign.created}")
    display.info(f"  Dir:     {state.campaign_dir}")
    display.console.print()

    table = Table(show_header=True, header_style="bold cyan", title="Players")
    table.add_column("Player ID")
    table.add_column("Joined")
    for pid, info in state.campaign.players.items():
        table.add_row(pid, info.joined)

    display.console.print(table)

    # Show pending truth proposals if any
    pending = state.campaign.pending_truth_proposals
    if pending:
        display.console.print()
        display.console.print(f"  [bold {COOP_TRUTH}]Pending Truth Proposals:[/bold {COOP_TRUTH}]")
        for cat, proposal in pending.items():
            display.console.print(
                f"  [dim]•[/dim] [{HINT_COMMAND}]{cat}[/{HINT_COMMAND}]  "
                f"[dim]by {proposal.proposer}[/dim]  {proposal.option_summary}"
            )
        display.console.print(
            "  [dim]Use /truths accept [category] to agree, or /truths counter to propose an alternative.[/dim]"
        )


def _handle_leave(state: GameState) -> None:
    """Leave the current campaign and return to solo mode."""
    if state.campaign is None:
        display.warn("You are not in a campaign.")
        return

    name = state.campaign.name
    state.campaign = None
    state.campaign_dir = None

    state.sync = LocalAdapter(state.character.name)

    display.info(f"Left campaign '{name}'. Playing in solo mode.")


def _show_no_campaign_help() -> None:
    content = (
        "[bold]Co-op Campaign Mode[/bold]\n\n"
        "You are currently playing solo. Start or join a campaign to play with others.\n\n"
        f"  [{HINT_COMMAND}]/campaign start[/{HINT_COMMAND}]   — begin your adventure (solo, create co-op, or join)\n"
        f"  [{HINT_COMMAND}]/campaign create[/{HINT_COMMAND}]  — create a new campaign (you become the first player)\n"
        f"  [{HINT_COMMAND}]/campaign join[/{HINT_COMMAND}]    — join an existing campaign\n\n"
        "Campaign files are shared via a common directory (Dropbox, Syncthing, etc.).\n"
        "Each player keeps their own character save; events sync via JSONL log files."
    )
    display.console.print(Panel(content, border_style=BORDER_REFERENCE, padding=(1, 2)))
