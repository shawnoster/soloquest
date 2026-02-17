"""Asset command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from soloquest.engine.assets import fuzzy_match_asset
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState


def handle_asset(state: GameState, args: list[str], _flags: set[str]) -> None:
    """Display asset information or list available assets."""
    if not args:
        # List all assets by category
        _list_assets(state)
        return

    query = "_".join(args).lower()
    matches = fuzzy_match_asset(query, state.assets)

    if not matches:
        display.error(f"Asset not found: '{' '.join(args)}'")
        display.info("Use /asset with no args to see all available assets.")
        return

    if len(matches) > 1:
        names = ", ".join(a.name for a in matches)
        display.warn(f"Multiple matches: {names}. Be more specific.")
        return

    asset = matches[0]
    _display_asset_details(asset)


def _list_assets(state: GameState) -> None:
    """List all available assets grouped by category."""
    if not state.assets:
        display.warn("No assets available.")
        return

    # Group by category
    categories: dict[str, list] = {}
    for asset in state.assets.values():
        cat = asset.category.replace("_", " ").title()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(asset)

    display.console.print("\n[bold cyan]Available Assets[/bold cyan]")
    display.console.print("Use /asset [name] to view details (e.g., /asset starship)\n")

    for category in sorted(categories.keys()):
        asset_list = categories[category]
        asset_names = ", ".join(sorted(a.name for a in asset_list))
        display.console.print(f"[bold]{category}:[/bold] {asset_names}")


def _display_asset_details(asset) -> None:
    """Display detailed information about an asset."""
    from soloquest.models.asset import Asset

    if not isinstance(asset, Asset):
        return

    # Build the panel content
    lines = []

    # Category and shared status
    category = asset.category.replace("_", " ").title()
    lines.append(f"[dim]Category: {category}[/dim]")

    if asset.shared:
        lines.append("[dim]Shared Asset[/dim]")

    # Inputs (custom fields)
    if asset.inputs:
        lines.append("")
        lines.append(f"[bold]Inputs:[/bold] {', '.join(asset.inputs)}")

    # Condition meters/tracks
    if asset.tracks:
        lines.append("")
        lines.append("[bold]Condition Meters:[/bold]")
        for track_name, (min_val, max_val) in asset.tracks.items():
            lines.append(f"  • {track_name.title()}: {min_val}–{max_val}")

    # Abilities
    if asset.abilities:
        lines.append("")
        lines.append("[bold]Abilities:[/bold]")
        for i, ability in enumerate(asset.abilities, 1):
            enabled_marker = "●" if ability.enabled else "○"
            lines.append(
                f"  {enabled_marker} [dim]{i}.[/dim] {display.render_game_text(ability.text)}"
            )

    body = "\n".join(lines)
    display.console.print(
        Panel(body, title=f"[bold]{asset.name.upper()}[/bold]", border_style="bright_magenta")
    )
