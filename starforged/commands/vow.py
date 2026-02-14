"""Vow command handlers — create, progress, fulfill."""

from __future__ import annotations

from typing import TYPE_CHECKING

from starforged.models.vow import Vow, VowRank, fuzzy_match_vow
from starforged.ui import display

if TYPE_CHECKING:
    from starforged.loop import GameState

VOW_RANKS = [r.value for r in VowRank]


def handle_vow(state: GameState, args: list[str], flags: set[str]) -> None:
    """Create a new vow: /vow [rank] [description]"""
    if len(args) < 2:
        display.error("Usage: /vow [rank] [description]")
        display.info(f"Ranks: {', '.join(VOW_RANKS)}")
        return

    rank_raw = args[0].lower()
    # Partial match on rank
    rank_matches = [r for r in VOW_RANKS if r.startswith(rank_raw)]
    if not rank_matches:
        display.error(f"Unknown rank '{rank_raw}'. Valid: {', '.join(VOW_RANKS)}")
        return

    rank = VowRank(rank_matches[0])
    description = " ".join(args[1:])

    vow = Vow(description=description, rank=rank)
    state.vows.append(vow)

    display.success(f"Vow sworn [{rank.value}]: {description}")
    state.session.add_mechanical(f"Vow sworn [{rank.value}]: {description}")


def handle_progress(state: GameState, args: list[str], flags: set[str]) -> None:
    """Mark progress on a vow: /progress [partial vow name]"""
    active = [v for v in state.vows if not v.fulfilled]
    if not active:
        display.error("No active vows.")
        return

    if not args:
        # Show all vows and prompt
        _show_vows(active)
        display.error("Usage: /progress [vow name or number]")
        return

    query = " ".join(args)
    vow = _resolve_vow(query, active)
    if vow is None:
        return

    old_ticks = vow.ticks
    new_ticks = vow.mark_progress()
    tick_gain = new_ticks - old_ticks

    display.success(
        f"Progress marked on '{vow.description}' "
        f"(+{tick_gain} ticks → {vow.progress_score}/10 boxes)"
    )
    _show_vow_track(vow)
    state.session.add_mechanical(
        f"Progress [{vow.rank.value}] on '{vow.description}': {vow.progress_score}/10"
    )


def handle_fulfill(state: GameState, args: list[str], flags: set[str]) -> None:
    """Attempt to fulfill a vow via progress roll (delegated to move handler)."""
    from starforged.commands.move import handle_move

    # Route to the fulfill_your_vow move
    handle_move(state, ["fulfill", "your", "vow"], flags)


def _resolve_vow(query: str, vows: list[Vow]) -> Vow | None:
    if query.isdigit():
        idx = int(query) - 1
        if 0 <= idx < len(vows):
            return vows[idx]
        display.error(f"No vow at index {int(query)}.")
        return None

    matches = fuzzy_match_vow(query, vows)
    if not matches:
        display.error(f"No vow matching '{query}'.")
        return None
    if len(matches) > 1:
        display.warn("Multiple vows match. Be more specific:")
        for v in matches:
            display.info(f"  [{v.rank.value}] {v.description}")
        return None
    return matches[0]


def _show_vows(vows: list[Vow]) -> None:
    for i, v in enumerate(vows, 1):
        display.info(f"  [{i}] [{v.rank.value}] {v.description} ({v.progress_score}/10)")


def _show_vow_track(vow: Vow) -> None:
    boxes = vow.boxes_filled
    partial = vow.partial_ticks
    bar = "▓" * boxes + ("░" if partial else "") + "□" * (10 - boxes - (1 if partial else 0))
    display.info(f"  {bar}  {vow.progress_score}/10")
