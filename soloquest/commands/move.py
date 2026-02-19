"""Move command handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.prompt import Confirm, Prompt

from soloquest.engine.dice import MixedDice, roll_action_dice, roll_challenge_dice, roll_oracle
from soloquest.engine.moves import (
    MoveResult,
    OutcomeTier,
    check_match,
    resolve_move,
    resolve_outcome,
    would_momentum_improve,
)
from soloquest.ui import display
from soloquest.ui.theme import BORDER_ORACLE

if TYPE_CHECKING:
    from soloquest.loop import GameState


def fuzzy_match_move(query: str, move_data: dict, category_filter: str | None = None) -> list[str]:
    """Find moves matching a partial query string.

    Prioritizes exact matches, then prefix matches, then substring matches.
    If category_filter is provided, only matches moves in that category.
    """
    q = query.lower().replace(" ", "_").replace("-", "_")

    # Empty query returns no matches (unless filtering by category)
    if not q and not category_filter:
        return []

    exact_matches = []
    prefix_matches = []
    substring_matches = []

    category_filter_lower = category_filter.lower() if category_filter else ""

    for key in move_data:
        move = move_data[key]

        # Apply category filter if specified
        if category_filter and move.get("category", "").lower() != category_filter_lower:
            continue

        # If only filtering by category (no query), include all moves in category
        if not q:
            exact_matches.append(key)
            continue

        name_norm = move["name"].lower().replace(" ", "_")

        # Check for exact match first
        if q in (key, name_norm):
            exact_matches.append(key)
        # Then check for prefix match
        elif key.startswith(q) or name_norm.startswith(q):
            prefix_matches.append(key)
        # Finally check for substring match
        elif q in key or q in name_norm:
            substring_matches.append(key)

    # Return in priority order: exact > prefix > substring
    return exact_matches or prefix_matches or substring_matches


# ── Arg parsing ─────────────────────────────────────────────────────────────────


def _parse_move_args(args: list[str]) -> tuple[str, str | None, list[str]]:
    """Parse move args into (query, category_filter, query_parts)."""
    category_filter = None
    query_parts = []
    for arg in args:
        if ":" in arg:
            prefix, value = arg.split(":", 1)
            if prefix.lower() in ("category", "type", "cat"):
                category_filter = value.lower()
            else:
                query_parts.append(arg)
        else:
            query_parts.append(arg)
    query = "_".join(query_parts).lower() if query_parts else ""
    return query, category_filter, query_parts


def _display_no_match_error(
    category_filter: str | None, query_parts: list[str], args: list[str]
) -> None:
    if category_filter:
        display.error(
            f"No moves found in category '{category_filter}'"
            + (f" matching '{' '.join(query_parts)}'" if query_parts else "")
        )
    else:
        display.error(f"Move not found: '{' '.join(args)}'")
    display.info("Try /help moves to see available moves.")


# ── Dice mode ────────────────────────────────────────────────────────────────────


def _apply_dice_mode(dice, flags: set[str]) -> None:
    """Apply manual/auto dice mode flags if dice supports it."""
    if isinstance(dice, MixedDice):
        if "manual" in flags:
            dice.set_manual(True)
        elif "auto" in flags:
            dice.set_manual(False)


def _reset_dice_mode(dice) -> None:
    """Reset dice to auto mode."""
    if isinstance(dice, MixedDice):
        dice.set_manual(False)


# ── Move dispatch ────────────────────────────────────────────────────────────────


def handle_move(state: GameState, args: list[str], flags: set[str]) -> None:
    if not args:
        _list_all_moves(state.moves)
        return

    query, category_filter, query_parts = _parse_move_args(args)
    matches = fuzzy_match_move(query, state.moves, category_filter)

    if not matches:
        _display_no_match_error(category_filter, query_parts, args)
        return

    if len(matches) > 1:
        if category_filter and not query:
            _display_category_moves(state.moves, matches, category_filter)
        else:
            names = ", ".join(state.moves[k]["name"] for k in matches)
            display.warn(f"Multiple matches ({len(matches)}): {names}. Be more specific.")
        return

    move_key = matches[0]
    move = state.moves[move_key]

    _apply_dice_mode(state.dice, flags)
    _dispatch_move(state, move_key, move, flags)
    _reset_dice_mode(state.dice)


def _dispatch_move(state: GameState, move_key: str, move: dict, flags: set[str]) -> None:
    """Route a move to the appropriate handler based on its type."""
    move_name = move["name"]
    if move.get("oracle_roll"):
        _handle_ask_the_oracle(state, flags, move)
    elif move.get("special") == "forsake":
        _handle_forsake_vow(state)
    elif move.get("progress_roll"):
        _handle_progress_roll(state, move_key, move, flags)
    elif not move.get("stat_options"):
        _handle_narrative_move(move_name, move, state)
    else:
        _execute_action_roll(state, move, move_name, flags)


# ── Standard action roll ──────────────────────────────────────────────────────────


def _execute_action_roll(state: GameState, move: dict, move_name: str, flags: set[str]) -> None:
    """Execute a standard action roll move."""
    stat_options: list[str] = move.get("stat_options", [])
    stat = _choose_stat(stat_options, state)
    if stat is None:
        return

    stat_val = state.character.stats.get(stat)

    adds_raw = Prompt.ask("  Any adds?", default="0")
    try:
        adds = max(0, int(adds_raw))
    except ValueError:
        adds = 0

    dice_result = roll_action_dice(state.dice)
    if dice_result is None:
        display.info("  Move cancelled.")
        return
    action_die, c1, c2 = dice_result
    result = resolve_move(
        action_die=action_die,
        stat=stat_val,
        adds=adds,
        c1=c1,
        c2=c2,
        momentum=state.character.momentum,
    )

    result = _maybe_burn_momentum(state, result, action_die, stat_val, adds, c1, c2)
    mom_delta = _apply_move_momentum(result.outcome, move, state)
    outcome_text = _outcome_text(result.outcome, move)
    display.move_result_panel(
        move_name=move_name,
        stat_name=stat,
        result=result,
        outcome_text=outcome_text,
        mom_delta=mom_delta,
    )
    _log_move(state, move_name, stat, stat_val, result, c1, c2)

    if result.outcome == OutcomeTier.MISS and not result.match:
        _offer_pay_the_price(state, flags)


def _maybe_burn_momentum(
    state: GameState,
    result: MoveResult,
    action_die: int,
    stat_val: int,
    adds: int,
    c1: int,
    c2: int,
) -> MoveResult:
    """Offer momentum burn if it would improve the outcome. Returns updated result."""
    if not would_momentum_improve(result.outcome, state.character.momentum, c1, c2):
        return result

    from soloquest.engine.moves import momentum_burn_outcome

    burn_tier = momentum_burn_outcome(state.character.momentum, c1, c2)
    tier_label = {
        OutcomeTier.STRONG_HIT: "Strong Hit",
        OutcomeTier.WEAK_HIT: "Weak Hit",
        OutcomeTier.MISS: "Miss",
    }[burn_tier]
    display.warn(f"Burning momentum ({state.character.momentum:+d}) would upgrade to {tier_label}")
    if not Confirm.ask("  Burn momentum?", default=False):
        return result

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
    state.session.add_mechanical(f"Burned momentum ({old_mom:+d} → {state.character.momentum:+d})")
    return result


# ── Stat selection ─────────────────────────────────────────────────────────────


def _choose_stat(stat_options: list[str], state: GameState) -> str | None:
    """Choose a stat. Returns None if cancelled (Ctrl+C or typing 'cancel')."""
    display.info("  Which stat?")
    for i, s in enumerate(stat_options, 1):
        val = state.character.stats.get(s)
        display.info(f"    [{i}] {s.capitalize():<8} {val}")

    while True:
        try:
            raw = Prompt.ask("  Stat (or 'cancel')").strip().lower()
            if raw in ["cancel", "back", "quit", "exit"]:
                return None
            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(stat_options):
                    return stat_options[idx]
            elif raw in stat_options:
                return raw
            # prefix match
            prefix = [s for s in stat_options if s.startswith(raw)]
            if len(prefix) == 1:
                return prefix[0]
            display.error(f"Choose 1–{len(stat_options)} or type a stat name (or 'cancel').")
        except (KeyboardInterrupt, EOFError):
            display.console.print()
            return None


# ── Outcome helpers ────────────────────────────────────────────────────────────


def _outcome_text(outcome: OutcomeTier, move: dict) -> str:
    match outcome:
        case OutcomeTier.STRONG_HIT:
            return move.get("strong_hit", "Strong hit.")
        case OutcomeTier.WEAK_HIT:
            return move.get("weak_hit", "Weak hit.")
        case OutcomeTier.MISS:
            return move.get("miss", "Miss. Pay the Price.")


def _apply_move_momentum(outcome: OutcomeTier, move: dict, state: GameState) -> int:
    """Apply momentum bonus from move. Returns the delta applied (0 if none)."""
    delta = 0
    if outcome == OutcomeTier.STRONG_HIT:
        delta = move.get("momentum_on_strong", 0)
    elif outcome == OutcomeTier.WEAK_HIT:
        delta = move.get("momentum_on_weak", 0)

    if delta:
        new_mom = state.character.adjust_momentum(delta)
        state.session.add_mechanical(f"Momentum {delta:+d} (now {new_mom:+d})")

    return delta


def _log_move(
    state: GameState,
    move_name: str,
    stat: str,
    stat_val: int,
    result: MoveResult,
    c1: int,
    c2: int,
) -> None:
    if result.burned_momentum:
        roll_str = f"momentum({result.momentum_used:+d})"
    else:
        parts = [f"d6({result.action_die})", f"{stat}({stat_val})"]
        if result.adds:
            parts.append(f"adds({result.adds})")
        roll_str = "+".join(parts)

    outcome_str = {
        OutcomeTier.STRONG_HIT: "STRONG HIT",
        OutcomeTier.WEAK_HIT: "WEAK HIT",
        OutcomeTier.MISS: "MISS",
    }[result.outcome]

    match_str = " ⚡MATCH" if result.match else ""
    log = (
        f"**{move_name}** | {roll_str} = {result.action_score} "
        f"vs [{c1}, {c2}] → {outcome_str}{match_str}"
    )
    state.session.add_move(log)


# ── Pay the Price ──────────────────────────────────────────────────────────────


def _offer_pay_the_price(state: GameState, flags: set[str]) -> None:
    """On a miss, offer to roll Pay the Price oracle."""
    display.console.print()
    if Confirm.ask("  Roll Pay the Price oracle?", default=True):
        from soloquest.engine.dice import roll_oracle

        table = state.oracles.get("pay_the_price")
        if not table:
            display.warn("Pay the Price oracle not found in data.")
            return
        roll = roll_oracle(state.dice)
        if roll is None:
            display.info("  Oracle roll cancelled.")
            return
        result = table.lookup(roll)
        display.oracle_result_panel(table.name, roll, result)
        state.session.add_oracle(f"Oracle [Pay the Price] roll {roll} → {result}")


# ── Progress rolls ─────────────────────────────────────────────────────────────


def _select_vow(state: GameState):
    """Prompt the player to choose an active vow. Returns the vow or None."""
    from soloquest.models.vow import fuzzy_match_vow

    active = [v for v in state.vows if not v.fulfilled]
    if not active:
        display.error("You have no active vows.")
        return None

    display.info("  Which vow?")
    for i, v in enumerate(active, 1):
        display.info(
            f"    [{i}] [{v.rank.value}] {v.description}  (progress {v.progress_score}/10)"
        )

    raw = Prompt.ask("  Vow number or name")
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(active):
            return active[idx]
    else:
        matches = fuzzy_match_vow(raw, active)
        if matches:
            return matches[0]

    display.error("Vow not found.")
    return None


def _resolve_progress_selection(state: GameState, move_key: str) -> tuple[object, int] | None:
    """Return (vow_or_None, progress_score), or None if the player cancels."""
    if move_key in ("fulfill_your_vow", "forsake_your_vow"):
        vow = _select_vow(state)
        if vow is None:
            return None
        return vow, vow.progress_score
    else:
        raw = Prompt.ask("  Progress score (0–10)")
        try:
            return None, max(0, min(10, int(raw)))
        except ValueError:
            display.error("Enter a number 0–10.")
            return None


def _handle_progress_roll(state: GameState, move_key: str, move: dict, flags: set[str]) -> None:
    """Handle a progress roll (Fulfill Vow, Take Decisive Action, etc.)."""
    move_name = move["name"]

    selection = _resolve_progress_selection(state, move_key)
    if selection is None:
        return
    vow, progress_score = selection

    dice_result = roll_challenge_dice(state.dice)
    if dice_result is None:
        display.info("  Progress roll cancelled.")
        return
    c1, c2 = dice_result
    outcome = resolve_outcome(progress_score, c1, c2)
    match_flag = check_match(c1, c2)

    result = MoveResult(
        action_die=0,
        stat=progress_score,
        adds=0,
        action_score=progress_score,
        challenge_1=c1,
        challenge_2=c2,
        outcome=outcome,
        match=match_flag,
    )

    outcome_text = _outcome_text(outcome, move)
    display.move_result_panel(
        move_name=move_name,
        stat_name="progress",
        result=result,
        outcome_text=outcome_text,
        mom_delta=0,
        is_progress_roll=True,
    )

    if vow and outcome in (OutcomeTier.STRONG_HIT, OutcomeTier.WEAK_HIT):
        vow.fulfilled = True
        display.success(f"Vow fulfilled: {vow.description}")
        state.session.add_mechanical(f"Vow fulfilled: {vow.description}")

    outcome_str = {
        OutcomeTier.STRONG_HIT: "STRONG HIT",
        OutcomeTier.WEAK_HIT: "WEAK HIT",
        OutcomeTier.MISS: "MISS",
    }[outcome]
    match_str = " ⚡MATCH" if match_flag else ""
    state.session.add_move(
        f"**{move_name}** | progress({progress_score}) vs [{c1}, {c2}] → {outcome_str}{match_str}"
    )


# ── Special move handlers ──────────────────────────────────────────────────────


_ORACLE_ODDS: list[tuple[str, int]] = [
    ("Almost Certain", 90),
    ("Likely", 75),
    ("50/50", 50),
    ("Unlikely", 25),
    ("Small Chance", 10),
]


def _handle_ask_the_oracle(state: GameState, flags: set[str], move: dict | None = None) -> None:
    """Ask the Oracle — prompt for odds, roll d100, report yes/no."""
    import re

    from rich.console import Group
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text

    category = move.get("category", "") if move else ""
    category_display = category.replace("_", " ").title() if category else "Move"

    description = ""
    if move:
        description = move.get("description", "")
        description = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"**\1**", description)

    odds_text = Text("\nChoose the odds:\n", style="bold")
    for i, (name, threshold) in enumerate(_ORACLE_ODDS, 1):
        odds_text.append(f"  [{i}] {name}", style="")
        odds_text.append(f"  (yes if ≤ {threshold})\n", style="dim")

    content = Group(Markdown(description), odds_text) if description else odds_text
    display.console.print(
        Panel(
            content,
            title="[bold]Ask the Oracle[/bold]",
            subtitle=f"[dim]{category_display}[/dim]",
            border_style=BORDER_ORACLE,
        )
    )

    raw = Prompt.ask("  Odds")
    try:
        idx = int(raw.strip()) - 1
        if not 0 <= idx < len(_ORACLE_ODDS):
            raise ValueError
    except ValueError:
        display.error("  Invalid selection.")
        return

    odds_name, threshold = _ORACLE_ODDS[idx]

    result = roll_oracle(state.dice)
    if result is None:
        display.info("  Ask the Oracle cancelled.")
        return

    answer = "Yes" if result <= threshold else "No"
    color = "green" if answer == "Yes" else "red"
    display.console.print(
        f"  Oracle roll: [bold]{result}[/bold]  —  [{color}][bold]{answer}[/bold][/{color}]"
        f"  [dim]({odds_name}: yes if ≤ {threshold})[/dim]"
    )
    state.session.add_mechanical(f"Ask the Oracle ({odds_name}): rolled {result} → {answer}")


def _handle_forsake_vow(state: GameState) -> None:
    """Forsake Your Vow — remove a vow and suffer spirit loss."""
    from soloquest.models.vow import SPIRIT_COST, fuzzy_match_vow

    active = [v for v in state.vows if not v.fulfilled]
    if not active:
        display.error("No active vows to forsake.")
        return

    display.info("  Which vow will you forsake?")
    for i, v in enumerate(active, 1):
        cost = SPIRIT_COST.get(v.rank, 1)
        display.info(f"    [{i}] [{v.rank.value}] {v.description}  (spirit cost: -{cost})")

    raw = Prompt.ask("  Vow number or name")
    vow = None
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

    cost = SPIRIT_COST.get(vow.rank, 1)
    vow.fulfilled = True  # mark as resolved (fulfilled=True covers both outcomes)
    new_spirit = state.character.adjust_track("spirit", -cost)

    display.warn(f"Vow forsaken: {vow.description}")
    display.mechanical_update(f"Spirit -{cost} → {new_spirit}/5")
    state.session.add_mechanical(
        f"Vow forsaken [{vow.rank.value}]: {vow.description} | Spirit -{cost} (now {new_spirit})"
    )


def _list_all_moves(move_data: dict) -> None:
    """List all moves grouped by category."""
    categories: dict[str, list[str]] = {}
    for key, move in move_data.items():
        cat = move.get("category", "other")
        categories.setdefault(cat, []).append(key)

    for category in sorted(categories.keys()):
        _display_category_moves(move_data, categories[category], category)


def _display_category_moves(move_data: dict, keys: list[str], category: str) -> None:
    """Display a list of moves in a category with their short descriptions."""
    from rich.table import Table

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("name", style="bold cyan", no_wrap=True)
    table.add_column("stats", style="dim blue", no_wrap=True)
    table.add_column("desc", style="dim")

    for key in keys:
        move = move_data[key]
        name = move["name"]
        stat_options = move.get("stat_options", [])
        stats = "+".join(s[:3] for s in stat_options) if stat_options else "—"
        desc = move.get("description", "").replace("**", "")
        short = desc.split(". ")[0].split(".\n")[0].rstrip(".")
        if len(short) > 65:
            short = short[:62] + "..."
        table.add_row(name, stats, short)

    category_display = category.replace("_", " ").title()
    display.console.print(f"\n[bold]{category_display} Moves[/bold]")
    display.console.print(table)
    display.console.print()
    display.info("  Use /move [name] to play a move.")


def _handle_narrative_move(move_name: str, move: dict, state: GameState) -> None:
    """Handle narrative/procedural moves that don't require dice rolls."""
    from rich.markdown import Markdown
    from rich.panel import Panel

    description = move.get("description", "")
    category = move.get("category", "")

    # Format category for display
    category_display = category.replace("_", " ").title() if category else "Move"

    # Strip dataforged cross-reference URLs before Markdown rendering.
    # [Move Name](Starforged/Moves/...) → Move Name (plain text).
    # This preserves table/bullet/bold formatting while avoiding non-functional links.
    import re

    description = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"**\1**", description)

    content = Markdown(description) if description else "[dim]No description available[/dim]"

    display.console.print(
        Panel(
            content,
            title=f"[bold]{move_name}[/bold]",
            subtitle=f"[dim]{category_display}[/dim]",
            border_style=BORDER_ORACLE,
        )
    )

    # Log to session
    state.session.add_move(f"**{move_name}** (narrative move)")
