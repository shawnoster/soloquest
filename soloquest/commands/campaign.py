"""Campaign command — create, join, and inspect co-op campaigns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from soloquest.state.campaign import (
    campaign_path,
    create_campaign,
    join_campaign,
    list_campaigns,
    load_campaign,
)
from soloquest.sync import FileLogAdapter
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def handle_campaign(state: GameState, args: list[str], flags: set[str]) -> None:
    """Manage co-op campaigns.

    Usage:
        /campaign            — show campaign status (or prompt to create/join)
        /campaign create     — create a new campaign
        /campaign join       — join an existing campaign
        /campaign status     — show current campaign info and players
        /campaign leave      — leave the current campaign (returns to solo mode)
    """
    sub = args[0].lower() if args else ""

    if sub == "create":
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


def _handle_leave(state: GameState) -> None:
    """Leave the current campaign and return to solo mode."""
    if state.campaign is None:
        display.warn("You are not in a campaign.")
        return

    name = state.campaign.name
    state.campaign = None
    state.campaign_dir = None

    from soloquest.sync import LocalAdapter

    state.sync = LocalAdapter(state.character.name)

    display.info(f"Left campaign '{name}'. Playing in solo mode.")


def _show_no_campaign_help() -> None:
    content = (
        "[bold]Co-op Campaign Mode[/bold]\n\n"
        "You are currently playing solo. Start or join a campaign to play with others.\n\n"
        "  [cyan]/campaign create[/cyan]  — create a new campaign (you become the first player)\n"
        "  [cyan]/campaign join[/cyan]    — join an existing campaign\n\n"
        "Campaign files are shared via a common directory (Dropbox, Syncthing, etc.).\n"
        "Each player keeps their own character save; events sync via JSONL log files."
    )
    display.console.print(Panel(content, border_style="cyan", padding=(1, 2)))
