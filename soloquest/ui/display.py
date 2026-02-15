"""Rich-based display helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from soloquest.engine.moves import MoveResult, OutcomeTier
from soloquest.models.character import DEBILITY_NAMES, Character
from soloquest.models.session import EntryKind, LogEntry
from soloquest.models.vow import Vow

console = Console()

# ── Palette ────────────────────────────────────────────────────────────────────
STRONG = "bold green"
WEAK = "bold yellow"
MISS_COLOR = "bold red"
MATCH_COLOR = "bold cyan"
MUTED = "dim"
STAT_COLOR = "bold blue"
HEADER = "bold white"


def splash() -> None:
    console.print()
    console.print(
        Panel(
            "[bold white]IRONSWORN: STARFORGED[/bold white]\n[dim]The Forge awaits.[/dim]",
            border_style="blue",
            padding=(1, 4),
        )
    )
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

    body = "\n".join(lines)
    console.print(Panel(body, title=f"[bold]{move_name.upper()}[/bold]", border_style="blue"))


def oracle_result_panel(table_name: str, roll: int, result: str) -> None:
    body = f"[dim]{roll}[/dim]  →  [bold]{result}[/bold]"
    console.print(
        Panel(body, title=f"[bold]ORACLE: {table_name.upper()}[/bold]", border_style="bright_cyan")
    )


def character_sheet(char: Character, vows: list[Vow], session_count: int, dice_mode: str) -> None:
    """Render full character sheet."""
    console.print()
    rule(char.name.upper())

    # Identity row
    if char.homeworld:
        console.print(f"  [dim]Homeworld:[/dim] {char.homeworld}")
    console.print(f"  [dim]Sessions:[/dim] {session_count}    [dim]Dice mode:[/dim] {dice_mode}")
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
    console.print("  " + _track_bar("Health", char.health, 5))
    console.print("  " + _track_bar("Spirit", char.spirit, 5))
    console.print("  " + _track_bar("Supply", char.supply, 5))
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
        console.print(
            "  " + "  /  ".join(a.asset_key.replace("_", " ").title() for a in char.assets)
        )
    else:
        console.print("  [dim]No assets.[/dim]")
    console.print()


def _track_bar(label: str, value: int, max_val: int) -> str:
    filled = "●" * value
    empty = "○" * (max_val - value)
    color = "green" if value > max_val // 2 else ("yellow" if value > 0 else "red")
    return f"{label:<8} [{color}]{filled}{empty}[/{color}]  [bold]{value}[/bold]/{max_val}"


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
