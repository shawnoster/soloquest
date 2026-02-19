"""Vow command handlers — create, progress, fulfill."""

from __future__ import annotations

from typing import TYPE_CHECKING

from soloquest.models.vow import Vow, VowRank, fuzzy_match_vow
from soloquest.ui import display

if TYPE_CHECKING:
    from soloquest.loop import GameState

VOW_RANKS = [r.value for r in VowRank]


def handle_vow(state: GameState, args: list[str], flags: set[str]) -> None:
    """Create a new vow: /vow [rank] [description]

    With --shared flag, creates a campaign-level vow visible to all players:
        /vow --shared [rank] [description]
    """
    # Detect --shared flag
    is_shared = "shared" in flags

    if len(args) < 2:
        display.error("Usage: /vow [rank] [description]")
        display.info(f"Ranks: {', '.join(VOW_RANKS)}")
        if state.campaign is not None:
            display.info("  Add --shared to create a campaign-level vow visible to all players.")
        return

    rank_raw = args[0].lower()
    # Partial match on rank
    rank_matches = [r for r in VOW_RANKS if r.startswith(rank_raw)]
    if not rank_matches:
        display.error(f"Unknown rank '{rank_raw}'. Valid: {', '.join(VOW_RANKS)}")
        return

    rank = VowRank(rank_matches[0])
    description = " ".join(args[1:])

    if is_shared:
        _handle_vow_shared(state, rank, description)
        return

    vow = Vow(description=description, rank=rank)
    state.vows.append(vow)

    display.success(f"Vow sworn [{rank.value}]: {description}")
    state.session.add_mechanical(f"Vow sworn [{rank.value}]: {description}")


def _handle_vow_shared(state: GameState, rank: VowRank, description: str) -> None:
    """Create a shared campaign vow."""
    from soloquest.sync.models import Event

    if state.campaign is None:
        display.warn("Shared vows require an active campaign. Use /campaign start first.")
        return

    vow = Vow(description=description, rank=rank, shared=True)
    state.campaign.shared_vows.append(vow)

    # Persist to campaign.toml
    if state.campaign_dir is not None:
        from soloquest.state.campaign import save_campaign

        save_campaign(state.campaign, state.campaign_dir)

    state.sync.publish(
        Event(
            player=state.character.name,
            type="shared_vow_created",
            data={"rank": rank.value, "description": description},
        )
    )

    display.success(f"Shared vow sworn [{rank.value}]: {description}")
    state.session.add_mechanical(f"Shared vow sworn [{rank.value}]: {description}")


def handle_progress(state: GameState, args: list[str], flags: set[str]) -> None:
    """Mark progress on a vow: /progress [partial vow name]

    Searches both personal and shared campaign vows.
    """
    shared = list(state.campaign.shared_vows) if state.campaign is not None else []
    active = [v for v in state.vows if not v.fulfilled] + [v for v in shared if not v.fulfilled]
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

    # If this is a shared vow, persist and publish the update
    if vow.shared and state.campaign is not None and state.campaign_dir is not None:
        from soloquest.state.campaign import save_campaign
        from soloquest.sync.models import Event

        save_campaign(state.campaign, state.campaign_dir)
        state.sync.publish(
            Event(
                player=state.character.name,
                type="shared_vow_progress",
                data={
                    "description": vow.description,
                    "progress_score": vow.progress_score,
                    "ticks": vow.ticks,
                },
            )
        )


def handle_fulfill(state: GameState, args: list[str], flags: set[str]) -> None:
    """Attempt to fulfill a vow via progress roll (delegated to move handler)."""
    from soloquest.commands.move import handle_move

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
    bar = "▓" * boxes + ("▒" if partial else "") + "□" * (10 - boxes - (1 if partial else 0))
    display.info(f"  {bar}  {vow.progress_score}/10")
