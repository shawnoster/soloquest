"""Rich-based display helpers."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from soloquest.engine.moves import MoveResult, OutcomeTier
from soloquest.models.character import DEBILITY_NAMES, TRACK_MAX, Character
from soloquest.models.session import EntryKind, LogEntry
from soloquest.models.vow import Vow

if TYPE_CHECKING:
    from soloquest.models.asset import Asset, CharacterAsset

console = Console()

# ── Palette ────────────────────────────────────────────────────────────────────
STRONG = "bold green"
WEAK = "bold yellow"
MISS_COLOR = "bold red"
MATCH_COLOR = "bold cyan"
MUTED = "dim"
STAT_COLOR = "bold blue"
HEADER = "bold white"


def render_game_text(text: str) -> str:
    """Convert dataforged markdown to Rich markup for in-panel display.

    Handles the subset of markdown used in dataforged move and asset text:
      **bold**        → [bold]text[/bold]
      [Name](url)     → [cyan]Name[/cyan]  (move cross-references)
      * item          → • item             (bullet lists)
    """
    text = re.sub(r"\*\*([^*]+)\*\*", r"[bold]\1[/bold]", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"[cyan]\1[/cyan]", text)
    text = re.sub(r"^  \* ", "  • ", text, flags=re.MULTILINE)
    text = re.sub(r"^\* ", "• ", text, flags=re.MULTILINE)
    return text


def splash(character: Character | None = None, vows: list[Vow] | None = None) -> None:
    if character:
        title_line = f"[bold white]{character.name.upper()}[/bold white]"
        if character.callsign:
            title_line += f"  [dim]«{character.callsign}»[/dim]"
        stats_line = (
            f"[dim]Health[/dim] {character.health}/{TRACK_MAX}  "
            f"[dim]Spirit[/dim] {character.spirit}/{TRACK_MAX}  "
            f"[dim]Supply[/dim] {character.supply}/{TRACK_MAX}  "
            f"[dim]Momentum[/dim] {character.momentum:+d}"
        )
        content = f"{title_line}\n{stats_line}"
        active_vows = [v for v in (vows or []) if not v.fulfilled]
        if active_vows:
            vow_lines = "\n".join(
                f"[dim]◈ {v.description}  {v.rank.value} {v.progress_score}/10[/dim]"
                for v in active_vows
            )
            content += f"\n\n{vow_lines}"
    else:
        content = "[bold white]SOLOQUEST[/bold white]"
    console.print()
    console.print(Panel(content, border_style="blue", padding=(1, 4)))
    console.print()


def rule(title: str = "") -> None:
    console.print(Rule(title, style="dim blue"))


def move_result_panel(
    move_name: str,
    result: MoveResult,
    outcome_text: str,
    stat_name: str = "",
    mom_delta: int = 0,
    is_progress_roll: bool = False,
) -> None:
    """Render a move result as a Rich panel."""
    match result.outcome:
        case OutcomeTier.STRONG_HIT:
            outcome_label = "◆ STRONG HIT"
            outcome_style = STRONG
        case OutcomeTier.WEAK_HIT:
            outcome_label = "◇ WEAK HIT"
            outcome_style = WEAK
        case OutcomeTier.MISS:
            outcome_label = "✕ MISS"
            outcome_style = MISS_COLOR

    lines: list[str] = []

    if is_progress_roll:
        lines.append(f"Progress score: [bold]{result.action_score}[/bold]")
    elif result.burned_momentum:
        lines.append(f"Burned momentum ({result.momentum_used:+d}) as action score")
        lines.append("")
    else:
        stat_label = stat_name.capitalize() if stat_name else "stat"
        adds_part = f" + {result.adds} (adds)" if result.adds else ""
        lines.append(
            f"Action:  d6({result.action_die}) + {stat_label}({result.stat}){adds_part}"
            f" = [bold]{result.action_score}[/bold]"
        )

    c1_style = "bold red" if not result.beats_c1 else "dim"
    c2_style = "bold red" if not result.beats_c2 else "dim"
    lines.append(
        f"Challenge: [{c1_style}]{result.challenge_1}[/{c1_style}]"
        f"  [{c2_style}]{result.challenge_2}[/{c2_style}]"
    )
    lines.append("")
    lines.append(f"[{outcome_style}]{outcome_label}[/{outcome_style}]")

    if result.match:
        lines.append(f"[{MATCH_COLOR}]⚡ MATCH — a dramatic turn[/{MATCH_COLOR}]")

    lines.append("")
    lines.append(f"[dim]{outcome_text}[/dim]")

    if mom_delta:
        lines.append("")
        lines.append(f"[dim]Momentum {mom_delta:+d}[/dim]")

    console.print(f"  [blue]└[/blue]  [bold]{move_name.upper()}[/bold]")
    for line in lines:
        console.print(f"     {line}")


def oracle_result_panel(table_name: str, roll: int, result: str) -> None:
    console.print(
        f"  [bright_cyan]└[/bright_cyan]  [dim]{table_name.upper()}[/dim]"
        f"  [dim]{roll}[/dim]  [dim]→[/dim]  [bold cyan]{result}[/bold cyan]"
    )


def oracle_result_panel_combined(results: list) -> None:
    """Display multiple oracle results, one per line."""
    max_name_width = max(len(r.table_name) for r in results)
    for r in results:
        padded_name = r.table_name.upper().ljust(max_name_width)
        console.print(
            f"  [bright_cyan]└[/bright_cyan]  [dim]{padded_name}[/dim]"
            f"  [dim]{r.roll:3d}[/dim]  [dim]→[/dim]  [bold cyan]{r.result}[/bold cyan]"
        )


def character_sheet(
    char: Character, vows: list[Vow], session_count: int, assets: dict | None = None
) -> None:
    """Render full character sheet."""
    console.print()
    rule(char.name.upper())

    # Identity row
    name_line = char.name.upper()
    if char.pronouns:
        name_line += f"  [dim]({char.pronouns})[/dim]"
    if char.callsign:
        name_line += f"  [dim]«{char.callsign}»[/dim]"
    console.print(f"  {name_line}")
    if char.homeworld:
        console.print(f"  [dim]Homeworld:[/dim] {char.homeworld}")
    console.print(f"  [dim]Sessions:[/dim] {session_count}")

    # Narrative flavour
    if char.backstory:
        console.print(f"  [dim]Backstory:[/dim] {char.backstory}")
    if char.look or char.act or char.wear:
        parts = []
        if char.look:
            parts.append(f"[dim]Look:[/dim] {char.look}")
        if char.act:
            parts.append(f"[dim]Act:[/dim] {char.act}")
        if char.wear:
            parts.append(f"[dim]Wear:[/dim] {char.wear}")
        console.print("  " + "    ".join(parts))
    if char.gear:
        console.print(f"  [dim]Gear:[/dim] {', '.join(char.gear)}")
    console.print()

    # Stats table
    stats_table = Table.grid(padding=(0, 3))
    stats_table.add_row(
        *[
            f"[{STAT_COLOR}]{k.capitalize():<7}[/{STAT_COLOR}][bold]{v}[/bold]"
            for k, v in char.stats.as_dict().items()
        ]
    )
    console.print("  ", end="")
    console.print(stats_table)
    console.print()

    # Tracks
    console.print("  " + _track_bar("Health", char.health, TRACK_MAX))
    console.print("  " + _track_bar("Spirit", char.spirit, TRACK_MAX))
    console.print("  " + _track_bar("Supply", char.supply, TRACK_MAX))
    console.print()

    # Momentum — shows current, max (affected by debilities), reset value
    mom_val = char.momentum
    mom_max = char.momentum_max
    mom_reset = char.momentum_reset
    # Map -6..+10 range to a visual bar (16 steps)
    mom_pos = mom_val + 6  # 0..16
    filled = "█" * mom_pos
    empty = "░" * (16 - mom_pos)
    mom_color = "green" if mom_val >= 0 else "red"
    debility_note = f"  [dim](max {mom_max}, reset {mom_reset})[/dim]" if char.debilities else ""
    console.print(
        f"  Momentum  [{mom_color}]{filled}{empty}[/{mom_color}]"
        f"  [bold]{mom_val:+d}[/bold]{debility_note}"
    )
    console.print()

    # Debilities
    if char.debilities:
        active = sorted(char.debilities)
        inactive = [d for d in DEBILITY_NAMES if d not in char.debilities]
        active_str = "  ".join(f"[bold red]{d.capitalize()}[/bold red]" for d in active)
        inactive_str = "  ".join(f"[dim]{d.capitalize()}[/dim]" for d in inactive)
        rule("Debilities")
        console.print(f"  {active_str}")
        if inactive_str:
            console.print(f"  {inactive_str}")
        console.print()
    else:
        rule("Debilities")
        console.print("  " + "  ".join(f"[dim]{d.capitalize()}[/dim]" for d in DEBILITY_NAMES))
        console.print()

    # Vows
    active_vows = [v for v in vows if not v.fulfilled]
    fulfilled_vows = [v for v in vows if v.fulfilled]
    rule("Vows")
    if active_vows:
        for vow in active_vows:
            _vow_row(vow)
    else:
        console.print("  [dim]No active vows.[/dim]")
    if fulfilled_vows:
        console.print()
        for vow in fulfilled_vows:
            console.print(f"  [dim]✓ [{vow.rank.value}] {vow.description}[/dim]")
    console.print()

    # Assets
    rule("Assets")
    if char.assets:
        for char_asset in char.assets:
            asset_def = assets.get(char_asset.asset_key) if assets else None
            console.print("  " + _asset_row(char_asset, asset_def))
    else:
        console.print("  [dim]No assets.[/dim]")
    console.print()


def _asset_row(char_asset: CharacterAsset, asset_def: Asset | None) -> str:
    """Build a single-line summary for an asset in the character sheet."""
    name = (
        asset_def.name if asset_def else char_asset.asset_key.replace("_", " ").title()
    )

    parts: list[str] = [f"{name:<16}"]

    # Optional input value (e.g., ship name)
    first_input = next(iter(char_asset.input_values.values()), "") if char_asset.input_values else ""
    if first_input:
        parts.append(f"[dim]«{first_input}»[/dim]")

    # Meter bar for the first track
    if asset_def and asset_def.tracks:
        track_name = next(iter(asset_def.tracks))
        _, max_val = asset_def.tracks[track_name]
        current = char_asset.track_values.get(track_name, max_val)
        parts.append(make_track_bar(track_name.title(), current, max_val))

    # Active conditions
    if char_asset.conditions:
        cond_str = "  ".join(
            f"[bold red]{c.title()}[/bold red]" for c in sorted(char_asset.conditions)
        )
        parts.append(f"[{cond_str}]")

    return "  ".join(parts)


def make_track_bar(label: str, value: int, max_val: int) -> str:
    """Return a Rich-markup meter bar string (usable inline or printed directly)."""
    filled = "●" * value
    empty = "○" * (max_val - value)
    color = "green" if value > max_val // 2 else ("yellow" if value > 0 else "red")
    return f"{label:<8} [{color}]{filled}{empty}[/{color}]  [bold]{value}[/bold]/{max_val}"


def _track_bar(label: str, value: int, max_val: int) -> str:
    return make_track_bar(label, value, max_val)


def _vow_row(vow: Vow) -> None:
    boxes = vow.boxes_filled
    partial = vow.partial_ticks
    # 10-box track: filled boxes, partial box indicator, empty boxes
    bar_parts = []
    bar_parts.append("▓" * boxes)
    if partial > 0:
        bar_parts.append("▒")  # partial fill indicator
        empty_boxes = 10 - boxes - 1
    else:
        empty_boxes = 10 - boxes
    bar_parts.append("□" * empty_boxes)
    bar = "".join(bar_parts)

    rank_color = {
        "troublesome": "green",
        "dangerous": "yellow",
        "formidable": "orange3",
        "extreme": "red",
        "epic": "bold red",
    }.get(vow.rank.value, "white")

    console.print(
        f"  [{rank_color}]{vow.rank.value.capitalize():<12}[/{rank_color}]"
        f" {bar}  [dim]{vow.progress_score}/10[/dim]  {vow.description}"
    )


def debility_status(char: Character) -> None:
    """Compact debility line for inline display after /debility."""
    active = sorted(char.debilities)
    if active:
        names = ", ".join(d.capitalize() for d in active)
        console.print(
            f"  [dim]Active debilities:[/dim] [bold red]{names}[/bold red]"
            f"  [dim](momentum max {char.momentum_max}, reset {char.momentum_reset})[/dim]"
        )
    else:
        console.print("  [dim]No active debilities.[/dim]")


def session_header(session_num: int, title: str) -> None:
    label = f"SESSION {session_num}" + (f" — {title}" if title else "")
    console.print()
    rule(label)
    console.print()


def log_entry(entry: LogEntry) -> None:
    match entry.kind:
        case EntryKind.JOURNAL:
            console.print(f"[white]{entry.text}[/white]")
        case EntryKind.MOVE:
            console.print(f"[dim blue]▸ {entry.text}[/dim blue]")
        case EntryKind.ORACLE:
            console.print(f"[bright_cyan]◈ {entry.text}[/bright_cyan]")
        case EntryKind.MECHANICAL:
            console.print(f"[dim italic]{entry.text}[/dim italic]")
        case EntryKind.NOTE:
            console.print(f"[yellow]📌 {entry.text}[/yellow]")


def recent_log(entries: list[LogEntry], n: int = 5) -> None:
    """Show last n journal/note entries for context."""
    recent = [e for e in entries if e.kind in (EntryKind.JOURNAL, EntryKind.NOTE)][-n:]
    if not recent:
        return
    rule("Recent Log")
    for entry in recent:
        log_entry(entry)
    console.print()


def mechanical_update(text: str) -> None:
    console.print(f"[dim]  ↳ {text}[/dim]")


def autosaved() -> None:
    """Subtle autosave indicator."""
    console.print("[dim]  ↳ autosaved[/dim]")


def error(text: str) -> None:
    console.print(f"[bold red]✗ {text}[/bold red]")


def warn(text: str) -> None:
    console.print(f"[yellow]⚠ {text}[/yellow]")


def success(text: str) -> None:
    console.print(f"[green]✓ {text}[/green]")


def info(text: str) -> None:
    console.print(f"[dim]{text}[/dim]")
