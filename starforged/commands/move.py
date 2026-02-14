"""Move command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.prompt import Confirm, Prompt

from starforged.engine.dice import MixedDice, roll_action_dice, roll_challenge_dice
from starforged.engine.moves import MoveResult, OutcomeTier, resolve_move, would_momentum_improve
from starforged.ui import display

if TYPE_CHECKING:
    from starforged.loop import GameState


def fuzzy_match_move(query: str, move_data: dict) -> list[str]:
    q = query.lower().replace(" ", "_").replace("-", "_")
    return [k for k in move_data if q in k or q in move_data[k]["name"].lower().replace(" ", "_")]


def handle_move(state: GameState, args: list[str], flags: set[str]) -> None:
    if not args:
        display.error("Usage: /move [name]  (e.g. /move strike)")
        return

    query = "_".join(args).lower()
    matches = fuzzy_match_move(query, state.moves)

    if not matches:
        display.error(f"Move not found: '{' '.join(args)}'")
        display.info("Try /help moves to see available moves.")
        return

    if len(matches) > 1:
        display.warn(f"Multiple matches: {', '.join(matches)}. Be more specific.")
        return

    move_key = matches[0]
    move = state.moves[move_key]
    move_name = move["name"]

    # Dice mode override flags
    dice = state.dice
    if isinstance(dice, MixedDice):
        if "manual" in flags:
            dice.set_manual(True)
        elif "auto" in flags:
            dice.set_manual(False)

    # Progress rolls (no action die, no stat)
    if move.get("progress_roll"):
        _handle_progress_roll(state, move_key, move, flags)
        return

    # Stat selection
    stat_options: list[str] = move.get("stat_options", [])
    if not stat_options:
        display.error(f"Move '{move_name}' has no stat options defined.")
        return

    stat = _choose_stat(stat_options, state)
    if stat is None:
        return

    stat_val = state.character.stats.get(stat)

    # Adds
    adds_raw = Prompt.ask("  Any adds?", default="0")
    try:
        adds = int(adds_raw)
    except ValueError:
        adds = 0

    # Roll
    action_die, c1, c2 = roll_action_dice(state.dice)
    result = resolve_move(
        action_die=action_die,
        stat=stat_val,
        adds=adds,
        c1=c1,
        c2=c2,
        momentum=state.character.momentum,
    )

    # Offer momentum burn if it would improve
    if would_momentum_improve(result.outcome, state.character.momentum, c1, c2):
        display.warn(
            f"Burning momentum ({state.character.momentum:+d}) would improve to "
            + ("Strong Hit" if result.outcome == OutcomeTier.MISS else "Strong Hit")
        )
        if Confirm.ask("  Burn momentum?", default=False):
            old_mom = state.character.burn_momentum()
            result = resolve_move(
                action_die=action_die,
                stat=stat_val,
                adds=adds,
                c1=c1,
                c2=c2,
                momentum=old_mom,
                burn=True,
            )
            state.session.add_mechanical(
                f"Burned momentum ({old_mom} → {state.character.momentum})"
            )

    # Determine outcome text
    outcome_text = _outcome_text(result.outcome, move)

    # Apply automatic momentum from strong/weak hits
    _apply_move_momentum(result.outcome, move, state)

    # Display
    display.move_result_panel(move_name, result, outcome_text)

    # Log
    action_score_str = (
        f"momentum({result.momentum_used})"
        if result.burned_momentum
        else f"{result.action_die}+{result.stat}+{result.adds}"
    )
    log_text = (
        f"**{move_name}** | {stat.capitalize()} {stat_val} | "
        f"{action_score_str} = {result.action_score} vs [{c1}, {c2}] → "
        f"{'STRONG HIT' if result.outcome == OutcomeTier.STRONG_HIT else 'WEAK HIT' if result.outcome == OutcomeTier.WEAK_HIT else 'MISS'}"
        + (" ⚡MATCH" if result.match else "")
    )
    state.session.add_move(log_text)

    # Reset mixed mode manual flag
    if isinstance(dice, MixedDice):
        dice.set_manual(False)


def _choose_stat(stat_options: list[str], state: GameState) -> str | None:
    display.info("  Which stat?")
    for i, s in enumerate(stat_options, 1):
        val = state.character.stats.get(s)
        display.info(f"    [{i}] {s.capitalize()} ({val})")

    while True:
        raw = Prompt.ask("  Stat")
        # Accept number or name
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(stat_options):
                return stat_options[idx]
        elif raw.lower() in stat_options:
            return raw.lower()
        # partial match
        matches = [s for s in stat_options if s.startswith(raw.lower())]
        if len(matches) == 1:
            return matches[0]
        display.error(f"Choose 1–{len(stat_options)} or type a stat name.")


def _outcome_text(outcome: OutcomeTier, move: dict) -> str:
    match outcome:
        case OutcomeTier.STRONG_HIT:
            return move.get("strong_hit", "Strong hit.")
        case OutcomeTier.WEAK_HIT:
            return move.get("weak_hit", "Weak hit.")
        case OutcomeTier.MISS:
            return move.get("miss", "Miss. Pay the Price.")


def _apply_move_momentum(outcome: OutcomeTier, move: dict, state: GameState) -> None:
    delta = 0
    if outcome == OutcomeTier.STRONG_HIT:
        delta = move.get("momentum_on_strong", 0)
    elif outcome == OutcomeTier.WEAK_HIT:
        delta = move.get("momentum_on_weak", 0)

    if delta:
        new_mom = state.character.adjust_momentum(delta)
        display.mechanical_update(f"Momentum {delta:+d} → {new_mom}")
        state.session.add_mechanical(f"Momentum {delta:+d} (now {new_mom})")


def _handle_progress_roll(state: GameState, move_key: str, move: dict, flags: set[str]) -> None:
    """Handle a progress roll (Fulfill Vow, Take Decisive Action, etc.)."""
    from starforged.models.vow import fuzzy_match_vow

    move_name = move["name"]

    # For vow-related progress rolls, ask which vow
    vow = None
    if move_key in ("fulfill_your_vow", "forsake_your_vow"):
        if not state.vows:
            display.error("You have no active vows.")
            return
        display.info("  Which vow?")
        active = [v for v in state.vows if not v.fulfilled]
        for i, v in enumerate(active, 1):
            display.info(
                f"    [{i}] [{v.rank.value}] {v.description} (progress: {v.progress_score}/10)"
            )
        raw = Prompt.ask("  Vow number or name")
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(active):
                vow = active[idx]
        else:
            matches = fuzzy_match_vow(raw, active)
            if matches:
                vow = matches[0]
        if vow is None:
            display.error("Vow not found.")
            return
        progress_score = vow.progress_score
    else:
        # Generic progress roll — ask for score
        raw = Prompt.ask("  Progress score (0–10)")
        try:
            progress_score = max(0, min(10, int(raw)))
        except ValueError:
            display.error("Enter a number 0–10.")
            return

    c1, c2 = roll_challenge_dice(state.dice)
    from starforged.engine.moves import check_match, resolve_outcome

    outcome = resolve_outcome(progress_score, c1, c2)
    match = check_match(c1, c2)

    result = MoveResult(
        action_die=0,
        stat=progress_score,
        adds=0,
        action_score=progress_score,
        challenge_1=c1,
        challenge_2=c2,
        outcome=outcome,
        match=match,
    )

    outcome_text = _outcome_text(outcome, move)
    display.move_result_panel(move_name, result, outcome_text)

    if vow and outcome in (OutcomeTier.STRONG_HIT, OutcomeTier.WEAK_HIT):
        vow.fulfilled = True
        display.success(f"Vow fulfilled: {vow.description}")

    log_text = (
        f"**{move_name}** | Progress {progress_score} vs [{c1}, {c2}] → "
        f"{'STRONG HIT' if outcome == OutcomeTier.STRONG_HIT else 'WEAK HIT' if outcome == OutcomeTier.WEAK_HIT else 'MISS'}"
        + (" ⚡MATCH" if match else "")
    )
    state.session.add_move(log_text)
