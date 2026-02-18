"""Asset command handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rich.panel import Panel

from soloquest.engine.assets import fuzzy_match_asset
from soloquest.models.asset import Asset, CharacterAsset
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState

_DELTA_RE = re.compile(r"^[+-]?\d+$")


def handle_asset(state: GameState, args: list[str], _flags: set[str]) -> None:
    """Display asset information, or view/update asset meters and conditions."""
    if not args:
        _list_assets(state)
        return

    # Try to resolve first arg against character's owned assets
    result = _find_char_asset(state, args[0])
    remaining = args[1:]

    if result is None:
        # Not a character asset — fall back to catalog lookup (read-only)
        if remaining:
            display.error(f"You don't own an asset matching '{args[0]}'.")
            display.info("Use /asset with no args to see all available assets.")
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
        _display_asset_details(matches[0])
        return

    char_asset, asset_def = result

    if not remaining:
        # Show asset detail with live meter values and conditions
        _display_char_asset_details(char_asset, asset_def)
        return

    # Parse remaining args to determine action
    _handle_asset_mutation(state, char_asset, asset_def, remaining)


def _find_char_asset(
    state: GameState, query: str
) -> tuple[CharacterAsset, Asset] | None:
    """Find a character-owned asset matching the query.

    Returns (CharacterAsset, Asset) on unique match, None if not found or ambiguous.
    """
    char = state.character
    if not char or not char.assets:
        return None

    q = query.lower().replace(" ", "_").replace("-", "_")

    exact: list[tuple[CharacterAsset, Asset]] = []
    prefix: list[tuple[CharacterAsset, Asset]] = []
    substring: list[tuple[CharacterAsset, Asset]] = []

    for ca in char.assets:
        asset_def = state.assets.get(ca.asset_key)
        if asset_def is None:
            continue
        key = ca.asset_key.lower()
        name_norm = asset_def.name.lower().replace(" ", "_")

        if q in (key, name_norm):
            exact.append((ca, asset_def))
        elif key.startswith(q) or name_norm.startswith(q):
            prefix.append((ca, asset_def))
        elif q in key or q in name_norm:
            substring.append((ca, asset_def))

    matches = exact or prefix or substring

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(asset_def.name for _, asset_def in matches)
        display.warn(f"Multiple asset matches: {names}. Be more specific.")
        return None
    return None


def _handle_asset_mutation(
    state: GameState,
    char_asset: CharacterAsset,
    asset_def: Asset,
    remaining: list[str],
) -> None:
    """Parse remaining args after the asset name and apply meter/condition change."""
    if len(remaining) == 1:
        arg = remaining[0]
        if _DELTA_RE.match(arg):
            # /asset [name] [+/-N] — primary meter
            _update_primary_meter(state, char_asset, asset_def, int(arg))
        else:
            # /asset [name] [condition] — toggle condition
            _toggle_asset_condition(state, char_asset, asset_def, arg)
    elif len(remaining) == 2:
        meter_name, delta_str = remaining
        if not _DELTA_RE.match(delta_str):
            display.error(f"Expected a number for the delta, got '{delta_str}'.")
            return
        _update_named_meter(state, char_asset, asset_def, meter_name, int(delta_str))
    else:
        display.error("Usage: /asset [name] [+/-N | meter +/-N | condition]")


def _update_primary_meter(
    state: GameState, char_asset: CharacterAsset, asset_def: Asset, delta: int
) -> None:
    if not asset_def.tracks:
        display.error(f"{asset_def.name} has no condition meters.")
        return
    track_name = next(iter(asset_def.tracks))
    _update_named_meter(state, char_asset, asset_def, track_name, delta)


def _update_named_meter(
    state: GameState,
    char_asset: CharacterAsset,
    asset_def: Asset,
    meter_name: str,
    delta: int,
) -> None:
    """Find a track by (partial) name, then apply delta."""
    q = meter_name.lower()
    found = None
    for tn in asset_def.tracks:
        if tn == q or tn.startswith(q) or q in tn:
            found = tn
            break

    if found is None:
        available = ", ".join(asset_def.tracks.keys()) or "none"
        display.error(
            f"No meter '{meter_name}' on {asset_def.name}. Available: {available}"
        )
        return

    min_val, max_val = asset_def.tracks[found]
    old_val = char_asset.track_values.get(found, max_val)
    new_val = char_asset.adjust_track(found, delta, min_val, max_val)

    label = f"{asset_def.name} {found.title()}"
    display.mechanical_update(f"{label} {old_val} → {new_val} ({delta:+d})")
    state.session.add_mechanical(f"[{asset_def.name}] {found.title()} {old_val} → {new_val} ({delta:+d})")


def _toggle_asset_condition(
    state: GameState,
    char_asset: CharacterAsset,
    asset_def: Asset,
    condition_name: str,
) -> None:
    is_active = char_asset.toggle_condition(condition_name)
    status = "ON" if is_active else "cleared"
    cond_display = condition_name.title()
    display.mechanical_update(f"{asset_def.name}: {cond_display} {status}")
    state.session.add_mechanical(f"[{asset_def.name}] Condition {cond_display}: {status}")


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


def _display_char_asset_details(char_asset: CharacterAsset, asset_def: Asset) -> None:
    """Display detailed asset info including live meter values and conditions."""
    lines = []

    category = asset_def.category.replace("_", " ").title()
    lines.append(f"[dim]Category: {category}[/dim]")

    if asset_def.shared:
        lines.append("[dim]Shared Asset[/dim]")

    if asset_def.inputs:
        lines.append("")
        lines.append(f"[bold]Inputs:[/bold] {', '.join(asset_def.inputs)}")
        for field_name in asset_def.inputs:
            val = char_asset.input_values.get(field_name.lower(), "")
            if val:
                lines.append(f"  [dim]«{val}»[/dim]")

    if asset_def.tracks:
        lines.append("")
        lines.append("[bold]Condition Meters:[/bold]")
        for track_name, (_min_val, max_val) in asset_def.tracks.items():
            current = char_asset.track_values.get(track_name, max_val)
            bar = display.make_track_bar(track_name.title(), current, max_val)
            lines.append(f"  {bar}")

    if char_asset.conditions:
        lines.append("")
        cond_str = "  ".join(
            f"[bold red]{c.title()}[/bold red]" for c in sorted(char_asset.conditions)
        )
        lines.append(f"[bold]Conditions:[/bold]  {cond_str}")

    if asset_def.abilities:
        lines.append("")
        lines.append("[bold]Abilities:[/bold]")
        for i, ability in enumerate(asset_def.abilities, 1):
            enabled_marker = "●" if ability.enabled else "○"
            lines.append(
                f"  {enabled_marker} [dim]{i}.[/dim] {display.render_game_text(ability.text)}"
            )

    body = "\n".join(lines)
    display.console.print(
        Panel(
            body,
            title=f"[bold]{asset_def.name.upper()}[/bold]",
            border_style="bright_magenta",
        )
    )


def _display_asset_details(asset: Asset) -> None:
    """Display detailed information about a catalog asset."""
    if not isinstance(asset, Asset):
        return

    lines = []

    category = asset.category.replace("_", " ").title()
    lines.append(f"[dim]Category: {category}[/dim]")

    if asset.shared:
        lines.append("[dim]Shared Asset[/dim]")

    if asset.inputs:
        lines.append("")
        lines.append(f"[bold]Inputs:[/bold] {', '.join(asset.inputs)}")

    if asset.tracks:
        lines.append("")
        lines.append("[bold]Condition Meters:[/bold]")
        for track_name, (min_val, max_val) in asset.tracks.items():
            lines.append(f"  • {track_name.title()}: {min_val}–{max_val}")

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
